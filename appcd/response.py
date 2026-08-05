# appcd/response.py
#
# WHAT: Maps a detection confidence score to one of four
#       response actions, mirroring Zhou et al.'s action
#       space (No Action / Service Scaling / Service
#       Replicas / Port Hopping).
# WHY:  This thesis's contribution is the collaborative
#       DETECTION layer. The response tier is chosen by a
#       simple, transparent confidence threshold rather than
#       a trained policy, kept honest rather than dressed up.

ACTION_TIERS = [
    (0.90, "port_hop"),
    (0.70, "service_replica"),
    (0.50, "rate_limit"),
    (0.0,  "no_action"),
]


def decide_action(confidence: float) -> str:
    """Returns the response action for a given attack confidence score."""
    for threshold, action in ACTION_TIERS:
        if confidence >= threshold:
            return action
    return "no_action"