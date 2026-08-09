# check_nodeB_probabilities.py
#
# WHAT: Loads the saved standalone model (trained on Node A
#       only) and computes its RAW predicted probabilities
#       (before thresholding) on Node B's, Node A's, and Node
#       D's validation data. This directly tests the reviewer's
#       hypothesis: is Node B's 0/750 positive-prediction rate
#       a feature-scaling artefact (predictions saturated near
#       0 regardless of input) or genuine generalisation
#       failure (predictions low but non-degenerate, i.e. the
#       model is making real, if wrong, judgements)?
#
# WHY THIS DISTINGUISHES THE TWO EXPLANATIONS:
#   - If normalisation were fit on Node A only and Node B's
#     inputs arrive unscaled, predicted probabilities would be
#     extremely tightly clustered near 0 (e.g. mean ~0.02,
#     >95% of flows below 0.05) -- a saturated, degenerate
#     output with almost no spread.
#   - If the model has genuinely never seen CIC-DDoS2019's
#     SYN-flood signature, predictions would be low but with
#     real spread (e.g. mean ~0.2-0.3, a meaningful fraction
#     above 0.10 even if all remain below the 0.5 threshold)
#     -- consistent with an under-confident but non-degenerate
#     judgement.

import numpy as np
from appcd.models import build_mlp

N_FEATURES = 42

print("Loading standalone model (trained on Node A only)...")
model = build_mlp(N_FEATURES)
model.load_weights("standalone_model.weights.h5")

for node_name, path in [("A", "edge_agent/data/node_A.npz"),
                          ("B", "edge_agent/data/node_B.npz"),
                          ("D", "edge_agent/data/node_D.npz")]:
    data = np.load(path)
    X_val = data["X_val"].astype(np.float32)
    y_val = data["y_val"]

    probs = model.predict(X_val, verbose=0).flatten()

    # Split by true label, since we care specifically about
    # attack-labelled flows' predicted probability (the ones
    # driving recall)
    attack_mask = y_val == 1
    attack_probs = probs[attack_mask]

    print(f"\n=== Node {node_name} ===")
    print(f"Total flows: {len(probs)}, Attack-labelled: {attack_mask.sum()}")
    print(f"ALL flows  -- mean prob: {probs.mean():.4f}, "
          f"% below 0.10: {(probs < 0.10).mean()*100:.1f}%, "
          f"% below 0.05: {(probs < 0.05).mean()*100:.1f}%")
    print(f"ATTACK-labelled flows only -- mean prob: {attack_probs.mean():.4f}, "
          f"% below 0.10: {(attack_probs < 0.10).mean()*100:.1f}%, "
          f"min: {attack_probs.min():.4f}, max: {attack_probs.max():.4f}, "
          f"std: {attack_probs.std():.4f}")