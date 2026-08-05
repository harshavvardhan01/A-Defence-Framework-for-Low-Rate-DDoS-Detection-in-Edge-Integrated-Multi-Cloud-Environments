# train_standalone.py
#
# WHAT: Trains a genuine standalone model on Node A's real
#       data, with NO federation involved — pure local
#       training, many epochs, no coordinator.
# WHY:  This is the fair "single-agent" condition your
#       supervisor requires — trained inside the SAME
#       codebase and on the SAME data as the federated
#       comparison, not pulled from a different paper's
#       environment.

import numpy as np
from appcd.models import build_mlp
from appcd.evaluation import compute_metrics

N_FEATURES = 42
EPOCHS = 30  # many local epochs, standing in for "trained alone, to convergence"

print("Loading Node A's real data...")
data = np.load("edge_agent/data/node_A.npz")
X_train, y_train = data["X_train"], data["y_train"]
X_val, y_val = data["X_val"], data["y_val"]

print(f"Training standalone model for {EPOCHS} epochs, no federation...")
model = build_mlp(N_FEATURES)
model.fit(X_train.astype(np.float32), y_train.astype(np.float32),
          epochs=EPOCHS, batch_size=256, verbose=1)

# Evaluate on the SAME held-out validation set the federated
# model was tested against
predictions = (model.predict(X_val.astype(np.float32), verbose=0) >= 0.5).astype(int).flatten()
metrics = compute_metrics(y_val, predictions)

print("\n" + "=" * 55)
print("STANDALONE MODEL — VALIDATION RESULTS")
print("=" * 55)
print(f"Accuracy:  {metrics['accuracy']:.2f}%")
print(f"Precision: {metrics['precision']:.2f}%")
print(f"Recall:    {metrics['recall']:.2f}%")
print(f"FPR:       {metrics['fpr']:.2f}%")

model.save_weights("standalone_model.weights.h5")
print("\nSaved to standalone_model.weights.h5")