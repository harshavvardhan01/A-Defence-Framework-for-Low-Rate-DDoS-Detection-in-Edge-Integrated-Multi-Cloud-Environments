# test_package.py
#
# WHAT: A smoke test — confirms the extracted appcd package
#       works correctly OUTSIDE Colab, using synthetic random
#       data. This does NOT test accuracy on real BCCC data —
#       that comes later. This only proves the code runs.

import numpy as np
from appcd.models import build_mlp
from appcd.federation import NodeTrainer, fedbn_average
from appcd.evaluation import compute_metrics

print("=" * 55)
print("APPCD PACKAGE SMOKE TEST")
print("=" * 55)

N_FEATURES = 41
SEED = 42
np.random.seed(SEED)

# ── Test 1: does the model build? ────────────────────
print("\n[1/4] Building a standalone model...")
model = build_mlp(N_FEATURES)
print(f"      OK — {model.count_params():,} parameters")

# ── Test 2: fake data for 3 nodes ────────────────────
print("\n[2/4] Generating synthetic data for 3 nodes...")
def fake_node_data(n_rows=200):
    X = np.random.rand(n_rows, N_FEATURES).astype(np.float32)
    y = np.random.randint(0, 2, n_rows)
    return X, y

X_A, y_A = fake_node_data()
X_B, y_B = fake_node_data()
X_D, y_D = fake_node_data()
print(f"      OK — 3 nodes, {len(y_A)} rows each")

# ── Test 3: does NodeTrainer train and return weights? ─
print("\n[3/4] Testing NodeTrainer.train_round() for each node...")
trainers = {
    "A": NodeTrainer(N_FEATURES),
    "B": NodeTrainer(N_FEATURES),
    "D": NodeTrainer(N_FEATURES),
}
global_weights = trainers["A"].model.get_weights()

node_weights = []
for key, (X, y) in zip(["A", "B", "D"], [(X_A, y_A), (X_B, y_B), (X_D, y_D)]):
    updated = trainers[key].train_round(global_weights, X, y)
    node_weights.append(updated)
    print(f"      Node {key}: trained one round, "
          f"returned {len(updated)} weight arrays")

# ── Test 4: does aggregation + evaluation work? ──────
print("\n[4/4] Testing fedbn_average() and compute_metrics()...")
bn_indices = trainers["A"].bn_indices
new_global = fedbn_average(node_weights, bn_indices)
print(f"      Aggregation OK — {len(new_global)} weight arrays returned")

y_pred_fake = np.random.randint(0, 2, len(y_A))
metrics = compute_metrics(y_A, y_pred_fake)
print(f"      Metrics OK — accuracy: {metrics['accuracy']:.2f}%, "
      f"precision: {metrics['precision']:.2f}%, "
      f"recall: {metrics['recall']:.2f}%, "
      f"FPR: {metrics['fpr']:.2f}%")

print("\n" + "=" * 55)
print("ALL TESTS PASSED — package works outside Colab")
print("=" * 55)