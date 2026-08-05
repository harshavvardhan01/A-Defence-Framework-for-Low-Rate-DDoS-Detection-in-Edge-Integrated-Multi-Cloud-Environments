# appcd/evaluation.py
#
# WHAT: Metric computation shared by every service.
# WHY:  Uses real sklearn precision_score/recall_score
#       directly — this fixes the mislabelled "precision"
#       bug found during the v2 review, where F1-score was
#       accidentally being reported as precision.

from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, confusion_matrix
)


def compute_metrics(y_true, y_pred):
    """
    Returns a dictionary of accuracy, precision, recall, and
    false-positive rate (FPR) — the operator-facing security
    metrics, not just accuracy alone.
    """
    accuracy = accuracy_score(y_true, y_pred) * 100
    precision = precision_score(y_true, y_pred, zero_division=0) * 100
    recall = recall_score(y_true, y_pred, zero_division=0) * 100

    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    fpr = (fp / (fp + tn) * 100) if (fp + tn) > 0 else 0.0

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "fpr": fpr,
    }