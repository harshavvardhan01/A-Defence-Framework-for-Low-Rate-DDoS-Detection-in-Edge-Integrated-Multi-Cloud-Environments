#  The federated learning core — persistent per-node
#       trainers, FedBN-aware weight averaging.

import numpy as np
import tensorflow as tf
from sklearn.utils.class_weight import compute_class_weight

from appcd.models import build_mlp
from appcd.evaluation import compute_metrics


def get_batchnorm_indices(model):
    """Flat weight-list indices belonging to BatchNormalization layers."""
    indices, idx = [], 0
    for layer in model.layers:
        n_weights = len(layer.get_weights())
        if isinstance(layer, tf.keras.layers.BatchNormalization):
            indices.extend(range(idx, idx + n_weights))
        idx += n_weights
    return indices


def fedbn_average(node_weight_list, bn_indices):
    """Averages Dense-layer weights with equal influence per node.
    BatchNorm entries are left as-is — each node's real BatchNorm
    statistics never leave that node."""
    n_nodes = len(node_weight_list)
    averaged = []
    for layer_index in range(len(node_weight_list[0])):
        if layer_index in bn_indices:
            averaged.append(node_weight_list[0][layer_index])
        else:
            layer_sum = np.zeros_like(
                node_weight_list[0][layer_index], dtype=np.float64)
            for node_weights in node_weight_list:
                layer_sum += node_weights[layer_index] / n_nodes
            averaged.append(layer_sum.astype(np.float32))
    return averaged


def _safe_class_weights(y):
    classes = np.unique(y)
    if len(classes) < 2:
        return None
    weights = compute_class_weight(
        "balanced", classes=np.array([0, 1]), y=y)
    return {0: float(weights[0]), 1: float(weights[1])}


class NodeTrainer:
    """One persistent trainer per edge node — keeps its model,
    warm Adam optimizer, and own BatchNorm state alive for the
    entire lifetime of the node. This is the fix that solved
    last week's coin-flip convergence instability."""

    def __init__(self, n_features, mu=0.05):
        self.n_features = n_features
        self.mu = mu
        self.model = build_mlp(n_features)
        self.bn_indices = get_batchnorm_indices(self.model)

    def _load_global_dense(self, global_weights):
        """MUTATES the real model. Only train_round() may call this."""
        current = self.model.get_weights()
        merged = [
            global_weights[i] if i not in self.bn_indices else current[i]
            for i in range(len(current))
        ]
        self.model.set_weights(merged)

    def get_bn_state(self):
        weights = self.model.get_weights()
        return [weights[i] for i in self.bn_indices]

    def train_round(self, global_weights, X_local, y_local,
                     epochs=1, batch_size=256):
        """The ONLY method allowed to permanently change what
        this node is training."""
        self._load_global_dense(global_weights)
        class_weights = _safe_class_weights(y_local)

        for _ in range(epochs):
            self.model.fit(
                X_local.astype(np.float32), y_local.astype(np.float32),
                epochs=1, batch_size=batch_size, verbose=0,
                class_weight=class_weights,
            )
            current_weights = self.model.get_weights()
            corrected = [
                w if i in self.bn_indices else w - self.mu * (w - g)
                for i, (w, g) in enumerate(zip(current_weights, global_weights))
            ]
            self.model.set_weights(corrected)

        return self.model.get_weights()

    def evaluate(self, X, y):
        """Evaluates the CURRENT real model — read-only, no mutation."""
        predictions = (
            self.model.predict(X.astype(np.float32), verbose=0) >= 0.5
        ).astype(int).flatten()
        return compute_metrics(y, predictions)

    def evaluate_candidate(self, candidate_dense_weights, X, y):
        """
        Evaluates a CANDIDATE model — candidate Dense weights + this
        node's OWN BatchNorm state — on a throwaway model.
        """
        shell = build_mlp(self.n_features)
        weights = [w.copy() for w in candidate_dense_weights]
        own_bn = self.get_bn_state()
        for i, bn_idx in enumerate(self.bn_indices):
            weights[bn_idx] = own_bn[i]
        shell.set_weights(weights)

        predictions = (
            shell.predict(X.astype(np.float32), verbose=0) >= 0.5
        ).astype(int).flatten()
        metrics = compute_metrics(y, predictions)

        del shell
        tf.keras.backend.clear_session()
        return metrics