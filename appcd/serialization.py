# Converts model weights (lists of numpy arrays) to and
#       from plain Python lists so they can be sent as JSON
#       over HTTP.
#  FastAPI/JSON cannot transport numpy arrays directly —
#       every weight array must become a nested Python list
#       before it crosses the network, and convert back again
#       on the receiving end.

import numpy as np


def weights_to_json(weights):
    """Converts a list of numpy arrays into JSON-safe nested lists."""
    return [w.tolist() for w in weights]


def weights_from_json(json_weights):
    """Converts JSON-safe nested lists back into numpy arrays."""
    return [np.array(w, dtype=np.float32) for w in json_weights]