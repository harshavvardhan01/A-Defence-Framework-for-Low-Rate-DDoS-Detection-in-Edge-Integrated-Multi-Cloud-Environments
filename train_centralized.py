
#
# Trains ONE standard (non-federated) model on Node A +
#       Node B + Node D's TRAINING data, literally pooled
#       together -- the one thing federation deliberately
#       avoids doing -- then evaluates it on the same pooled
#       validation set.


import numpy as np
from appcd.models import build_mlp
from appcd.evaluation import compute_metrics

N_FEATURES = 42
EPOCHS = 30  

print("Loading and pooling Node A, B, D training data...")
data_a = np.load("edge_agent/data/node_A.npz")
data_b = np.load("edge_agent/data/node_B.npz")
data_d = np.load("edge_agent/data/node_D.npz")


X_train = np.concatenate([data_a["X_train"], data_b["X_train"], data_d["X_train"]], axis=0)
y_train = np.concatenate([data_a["y_train"], data_b["y_train"], data_d["y_train"]], axis=0)

X_val = np.concatenate([data_a["X_val"], data_b["X_val"], data_d["X_val"]], axis=0)
y_val = np.concatenate([data_a["y_val"], data_b["y_val"], data_d["y_val"]], axis=0)

print(f"Pooled training set: {len(X_train)} flows")
print(f"Pooled validation set: {len(X_val)} flows "
      f"({int(y_val.sum())} attack, {int(len(y_val) - y_val.sum())} legitimate)")

print(f"\nTraining centralised model for {EPOCHS} epochs on pooled data...")
model = build_mlp(N_FEATURES)
model.fit(X_train.astype(np.float32), y_train.astype(np.float32),
          epochs=EPOCHS, batch_size=32, verbose=1)

predictions = (model.predict(X_val.astype(np.float32), verbose=0) >= 0.5).astype(int).flatten()
metrics = compute_metrics(y_val, predictions)

print("\n" + "=" * 55)
print("CENTRALISED MODEL — POOLED VALIDATION RESULTS")
print("=" * 55)
print(f"Accuracy:  {metrics['accuracy']:.2f}%")
print(f"Precision: {metrics['precision']:.2f}%")
print(f"Recall:    {metrics['recall']:.2f}%")
print(f"FPR:       {metrics['fpr']:.2f}%")

model.save_weights("centralized_model.weights.h5")
print("\nSaved to centralized_model.weights.h5")