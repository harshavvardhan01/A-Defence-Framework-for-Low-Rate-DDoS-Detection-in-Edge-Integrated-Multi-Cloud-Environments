# check_node_a_split.py
#
# WHAT: Reports the exact attack:benign count in Node A's
#       validation split, directly from the real data file --
#       resolving the "approx. 50:50" imprecision flagged in
#       Table 2, the same way Node B and Node D's exact splits
#       were already confirmed.

import numpy as np

data_a = np.load("edge_agent/data/node_A.npz")
y_val = data_a["y_val"]

attack_count = int(y_val.sum())
benign_count = int(len(y_val) - y_val.sum())

print(f"Node A validation set: {len(y_val)} total flows")
print(f"Attack: {attack_count}")
print(f"Benign: {benign_count}")
print(f"Ratio: {attack_count}:{benign_count}")