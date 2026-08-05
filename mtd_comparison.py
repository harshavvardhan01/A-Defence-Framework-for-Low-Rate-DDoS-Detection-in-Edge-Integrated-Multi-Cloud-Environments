# mtd_comparison.py
#
# WHAT: A fair, isolated comparison of the STANDALONE model
#       vs. the FEDERATED model, both trained locally and
#       evaluated on POOLED validation data from ALL THREE
#       real nodes (A, B, D) -- not just one node's own data
#       -- through the identical classification-and-response
#       pipeline. The ONLY variable that differs between the
#       two conditions is how the model was trained.
#
# WHY POOLED, MULTI-NODE EVALUATION (not just Node A's data):
#   An earlier version of this script tested both models only
#   against Node A's own validation split. That produced
#   IDENTICAL results for both conditions, because a model
#   trained directly on Node A's distribution fits Node A's
#   own held-out data well almost by definition -- it never
#   exercised the actual value federation provides, which is
#   generalising ACROSS heterogeneous environments (Node B's
#   CIC-DDoS2019 traffic, Node D's skewed BCCC traffic) that
#   the standalone model never saw during training. Testing
#   on pooled, multi-node data is what makes this comparison
#   meaningful, and matches the same methodology already used
#   for the RQ1 standalone-vs-federated result.
#
# WHY THIS REPLACES THE ORIGINAL VERSION (pre-dating both fixes):
#   The original version compared THIS system's live numbers
#   against numbers PRINTED in Zhou et al.'s paper -- two
#   different environments, two different datasets, two
#   different simulations. That is not a valid comparison
#   (see supervisor feedback, Table 7). This version compares
#   two conditions both measured HERE, on the SAME machine,
#   SAME pooled data, SAME code -- so any difference in the
#   results is attributable to the one thing that changed:
#   standalone vs. federated training.

import time
import numpy as np

from appcd.models import build_mlp
from appcd.evaluation import compute_metrics as compute_ml_metrics
from appcd.response import decide_action

N_FEATURES = 42
NODE_IDS = ["A", "B", "D"]  # test against ALL real, active nodes' data

STANDALONE_WEIGHTS = "standalone_model.weights.h5"
FEDERATED_WEIGHTS = "federated_model.weights.h5"


def load_model(weights_path):
    model = build_mlp(N_FEATURES)
    model.load_weights(weights_path)
    return model


def load_all_validation_data():
    """
    Loads and pools validation data from every real node. This
    is what actually exercises federation's cross-environment
    generalisation -- evaluating on a single node's own data
    would not, since that node's own distribution is exactly
    what a model trained on it alone is expected to fit well.
    Returns the pooled (X, y) pair AND a per-node dict for the
    breakdown printed later.
    """
    X_parts, y_parts, per_node = [], [], {}
    for node_id in NODE_IDS:
        data = np.load(f"edge_agent/data/node_{node_id}.npz")
        X_parts.append(data["X_val"])
        y_parts.append(data["y_val"])
        per_node[node_id] = (data["X_val"], data["y_val"])

    X_pooled = np.concatenate(X_parts, axis=0)
    y_pooled = np.concatenate(y_parts, axis=0)
    return X_pooled, y_pooled, per_node


def evaluate_condition(model, X_val, y_val, label):
    """
    Runs ONE model through the full evaluation on the POOLED
    multi-node data: real ML metrics (precision/recall/FPR/
    accuracy) AND the MTD action-selection pass (action
    distribution + per-flow decision latency). Returns both
    result sets so the caller can print them side-by-side
    against the other condition.
    """
    print(f"\nEvaluating {label} (pooled, all nodes)...")

    # ── Real ML metrics: identical methodology to RQ1 ────────
    predictions = (model.predict(X_val.astype(np.float32), verbose=0) >= 0.5
                   ).astype(int).flatten()
    ml_metrics = compute_ml_metrics(y_val, predictions)

    # ── MTD action selection + decision latency, per flow ────
    action_counts = {"no_action": 0, "rate_limit": 0,
                      "service_replica": 0, "port_hop": 0}
    latencies_ms = []

    for i in range(len(X_val)):
        X = X_val[i:i + 1].astype(np.float32)

        start = time.perf_counter()
        confidence = float(model.predict(X, verbose=0)[0][0])
        action = decide_action(confidence)
        elapsed_ms = (time.perf_counter() - start) * 1000

        action_counts[action] += 1
        latencies_ms.append(elapsed_ms)

    # Discard the first measurement (cold-start / graph-tracing
    # overhead, documented in Section 5.5) when reporting
    # steady-state latency.
    steady_state_latencies = latencies_ms[1:] if len(latencies_ms) > 1 else latencies_ms
    mean_latency = sum(steady_state_latencies) / len(steady_state_latencies)

    return {
        "label": label,
        "accuracy": ml_metrics["accuracy"],
        "precision": ml_metrics["precision"],
        "recall": ml_metrics["recall"],
        "fpr": ml_metrics["fpr"],
        "action_counts": action_counts,
        "n_flows": len(X_val),
        "cold_start_ms": latencies_ms[0] if latencies_ms else None,
        "mean_latency_ms": mean_latency,
    }


def evaluate_per_node(model, per_node_data, label):
    """
    Breaks the same model's performance down BY NODE, so the
    report can show WHERE a generalisation gap appears -- e.g.
    a standalone model scoring well on its own node but poorly
    on nodes it never trained on, versus a federated model
    scoring consistently across all three.
    """
    print(f"\n  Per-node breakdown -- {label}:")
    results = {}
    for node_id, (X_n, y_n) in per_node_data.items():
        preds = (model.predict(X_n.astype(np.float32), verbose=0) >= 0.5
                 ).astype(int).flatten()
        m = compute_ml_metrics(y_n, preds)
        results[node_id] = m
        print(f"    Node {node_id}: accuracy {m['accuracy']:.2f}%   "
              f"recall {m['recall']:.2f}%   FPR {m['fpr']:.2f}%")
    return results


def print_result_block(result):
    n = result["n_flows"]
    print(f"\n  {result['label']}")
    print(f"    Accuracy:   {result['accuracy']:.2f}%")
    print(f"    Precision:  {result['precision']:.2f}%")
    print(f"    Recall:     {result['recall']:.2f}%")
    print(f"    FPR:        {result['fpr']:.2f}%")
    print(f"    Action distribution (of {n} flows):")
    for action, count in result["action_counts"].items():
        pct = 100.0 * count / n
        print(f"      {action:<18} {count:>4}  ({pct:5.1f}%)")
    print(f"    Cold-start decision latency: {result['cold_start_ms']:.2f} ms")
    print(f"    Steady-state decision latency: {result['mean_latency_ms']:.2f} ms")


def main():
    print("=" * 65)
    print("FAIR COMPARISON: STANDALONE vs. FEDERATED")
    print("=" * 65)
    print("Both conditions below are evaluated LOCALLY, on POOLED")
    print(f"validation data from all {len(NODE_IDS)} real nodes "
          f"({', '.join(NODE_IDS)}), through the")
    print("IDENTICAL classification-and-response pipeline. The only")
    print("variable that differs is how each model was trained.")

    X_val, y_val, per_node_data = load_all_validation_data()
    print(f"\nPooled validation set: {len(X_val)} real flows "
          f"({int(y_val.sum())} attack, {int(len(y_val) - y_val.sum())} legitimate)")
    for node_id, (X_n, y_n) in per_node_data.items():
        print(f"  Node {node_id}: {len(X_n)} flows "
              f"({int(y_n.sum())} attack, {int(len(y_n) - y_n.sum())} legitimate)")

    standalone_model = load_model(STANDALONE_WEIGHTS)
    federated_model = load_model(FEDERATED_WEIGHTS)

    standalone_result = evaluate_condition(
        standalone_model, X_val, y_val, "STANDALONE (trained alone, no federation)")
    federated_result = evaluate_condition(
        federated_model, X_val, y_val, "FEDERATED (trained via FedBN + FedProx)")

    print("\n" + "=" * 65)
    print("POOLED RESULTS (all nodes combined)")
    print("=" * 65)
    print_result_block(standalone_result)
    print_result_block(federated_result)

    print("\n" + "=" * 65)
    print("PER-NODE BREAKDOWN -- shows WHERE any generalisation gap appears")
    print("=" * 65)
    evaluate_per_node(standalone_model, per_node_data,
                       "STANDALONE (trained alone, no federation)")
    evaluate_per_node(federated_model, per_node_data,
                       "FEDERATED (trained via FedBN + FedProx)")

    # ── Side-by-side summary table, plain text, no colour ────
    print("\n" + "=" * 65)
    print("SUMMARY -- STANDALONE vs. FEDERATED (pooled, same pipeline)")
    print("=" * 65)
    print(f"{'Metric':<28}{'Standalone':>16}{'Federated':>16}")
    print("-" * 65)
    print(f"{'Accuracy (%)':<28}{standalone_result['accuracy']:>16.2f}"
          f"{federated_result['accuracy']:>16.2f}")
    print(f"{'Precision (%)':<28}{standalone_result['precision']:>16.2f}"
          f"{federated_result['precision']:>16.2f}")
    print(f"{'Recall (%)':<28}{standalone_result['recall']:>16.2f}"
          f"{federated_result['recall']:>16.2f}")
    print(f"{'FPR (%)':<28}{standalone_result['fpr']:>16.2f}"
          f"{federated_result['fpr']:>16.2f}")
    print(f"{'Decision latency (ms)':<28}{standalone_result['mean_latency_ms']:>16.2f}"
          f"{federated_result['mean_latency_ms']:>16.2f}")

    print("\nNOTE: QoS and resource-cost figures are deliberately not")
    print("reported as single numbers here. mtd_sensitivity.py shows")
    print("these vary by 70+ percentage points across reasonable")
    print("simulation-parameter assumptions -- they are discussed")
    print("qualitatively in the report rather than quantified here.")

    print("\nNOTE: Zhou et al.'s reported figures are not included in")
    print("this table. Their measurements were taken in a different")
    print("environment (different dataset, hardware, and response")
    print("policy) and are discussed as context in the report text,")
    print("not as a directly comparable result.")


if __name__ == "__main__":
    main()