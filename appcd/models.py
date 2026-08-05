# appcd/models.py
#
# WHAT: Defines the MLP architecture used by every node.
# WHY:  This is the exact model from the Colab notebook,
#       extracted so it can be imported by any service —
#       not just run inside a notebook cell.

import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, BatchNormalization


def build_mlp(n_features):
    """Builds and compiles a fresh MLP with the given input size."""
    model = Sequential([
        Dense(256, activation="relu", input_shape=(n_features,)),
        BatchNormalization(),
        Dropout(0.2),

        Dense(128, activation="relu"),
        BatchNormalization(),
        Dropout(0.2),

        Dense(64, activation="relu"),
        Dropout(0.2),

        Dense(1, activation="sigmoid"),
    ])
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
        loss="binary_crossentropy",
        metrics=["accuracy"],
    )
    return model