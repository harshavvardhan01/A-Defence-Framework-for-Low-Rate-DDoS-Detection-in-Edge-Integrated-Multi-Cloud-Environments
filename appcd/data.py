# Returns real BCCC/CIC-DDoS2019 shards if the exported
#       .npz file exists for a node; falls back to synthetic
#       random data otherwise .


import os
import numpy as np

NODE_SEEDS = {"A": 1, "B": 2, "C": 3, "D": 4}
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "edge_agent", "data")


def get_node_data(node_id, n_features=41, n_rows=500, val_fraction=0.15):
    
    real_path = os.path.abspath(
        os.path.join(DATA_DIR, f"node_{node_id}.npz"))

    if os.path.exists(real_path):
        data = np.load(real_path)
        return (
            data["X_train"].astype(np.float32),
            data["y_train"].astype(np.int64),
            data["X_val"].astype(np.float32),
            data["y_val"].astype(np.int64),
        )

    # ── Synthetic fallback ──────────
    seed = NODE_SEEDS.get(node_id, 0)
    rng = np.random.RandomState(seed)
    X = rng.rand(n_rows, n_features).astype(np.float32)
    y = rng.randint(0, 2, n_rows)

    cut = int(n_rows * (1 - val_fraction))
    return X[:cut], y[:cut], X[cut:], y[cut:]