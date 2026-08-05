# appcd/reward.py
#
# WHAT: Scores a completed ServiceState run into security %,
#       QoS %, and resource cost — same four-term structure
#       as Zhou et al.'s Eq. 4.
# WHY:  Turns raw simulation numbers into the two percentages
#       directly comparable to the baseline paper.

def compute_metrics(state):
    security_pct = 100.0 * (1 - state.successful_attacks / max(state.total_attacks, 1))
    qos_pct = 100.0 * (1 - state.blocked_legitimate / max(state.total_legitimate, 1))

    return {
        "security_pct": round(security_pct, 2),
        "qos_pct": round(qos_pct, 2),
        "avg_capacity": round(state.capacity, 2),
        "avg_response_time_ms": round(state.response_time_ms, 2),
        "resource_cost": round(state.resource_cost, 2),
        "total_attacks": state.total_attacks,
        "total_legitimate": state.total_legitimate,
    }


def improvement(undefended: dict, defended: dict):
    sec_gain = defended["security_pct"] - undefended["security_pct"]
    qos_gain = defended["qos_pct"] - undefended["qos_pct"]
    return {
        "security_improvement_pp": round(sec_gain, 2),
        "qos_improvement_pp": round(qos_gain, 2),
        "resource_cost_increase": round(
            defended["resource_cost"] - undefended["resource_cost"], 2),
    }