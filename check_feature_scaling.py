# check_feature_scaling.py
#
# WHAT: Directly compares the per-feature statistics (mean,
#       std, min, max) of Node A, Node B, and Node D's saved
#       training data -- this tests the ACTUAL data currently
#       being fed to the model, rather than trying to
#       reconstruct what an old preprocessing script did.
#
# HOW TO READ THE RESULT:
#   If normalisation is correct (fit per-node, or fit once
#   globally on genuinely comparable raw features), all three
#   nodes' features should look statistically similar --
#   roughly the same mean/std range, no node wildly different
#   from the other two.
#
#   If Node B's features are on a visibly different scale
#   (e.g. Node A/D show mean~0, std~1, but Node B shows mean
#   in the hundreds or std wildly larger/smaller), that is
#   direct, physical evidence of a scaling mismatch -- Node
#   B's inputs are arriving in different units or ranges than
#   the model was calibrated for.

import numpy as np

print(f"{'Node':<6}{'Feature stat (mean of per-feature means)':<45}{'(mean of per-feature stds)'}")
print("=" * 90)

for node_name, path in [("A", "edge_agent/data/node_A.npz"),
                          ("B", "edge_agent/data/node_B.npz"),
                          ("D", "edge_agent/data/node_D.npz")]:
    data = np.load(path)
    X_train = data["X_train"]

    per_feature_mean = X_train.mean(axis=0)
    per_feature_std = X_train.std(axis=0)

    print(f"{node_name:<6}"
          f"{'mean='+str(round(per_feature_mean.mean(),4)):<25}"
          f"min/max: {per_feature_mean.min():.3f}/{per_feature_mean.max():.3f}    "
          f"std={per_feature_std.mean():.4f} (min/max: {per_feature_std.min():.3f}/{per_feature_std.max():.3f})")

print()
print("If Node A and Node D look similar to each other but Node B looks")
print("wildly different (much larger mean/std magnitude, or a very")
print("different min/max range), that points to a scaling mismatch.")
print("If all three look broadly similar, scaling is very likely fine,")
print("and Node B's failure is a genuine generalisation gap instead.")

print()
print("=" * 90)
print("First 5 raw feature values, first row, each node (for a quick eyeball check):")
for node_name, path in [("A", "edge_agent/data/node_A.npz"),
                          ("B", "edge_agent/data/node_B.npz"),
                          ("D", "edge_agent/data/node_D.npz")]:
    data = np.load(path)
    print(f"Node {node_name}: {data['X_train'][0][:5]}")