# mtd_sensitivity.py
#
# WHAT: Runs the undefended-vs-defended comparison across
#       THREE different, explicitly labelled parameter sets,
#       to check whether the QoS/security findings hold
#       directionally, not just under one chosen configuration.
# WHY:  A single-parameter-set result cannot survive "how did
#       you calibrate this" in a viva. This can.
import os
import numpy as np
import requests

from appcd.simulation import ServiceState
from appcd.reward import compute_metrics, improvement

NODE_URL = "http://54.194.2.155:8000"
TOKEN = os.environ.get("APPCD_TOKEN", "")

if not TOKEN:
    raise ValueError("Set APPCD_TOKEN as an environment variable before running this script")

data = np.load("edge_agent/data/node_A.npz")
X_val, y_val = data["X_val"], data["y_val"]
N = len(X_val)

# Pre-fetch every flow's action ONCE — reused across all three
# parameter sets so we're testing SENSITIVITY, not re-running
# inference three times unnecessarily.
print(f"Classifying {N} flows once, reusing across parameter sets...")
actions = []
for i in range(N):
    resp = requests.post(f"{NODE_URL}/classify",
                          json={"features": X_val[i].tolist()},
                          headers={"X-APPCD-Token": TOKEN})
    actions.append(resp.json()["action"])
print("Done.\n")

configs = [
    {"name": "Baseline",        "attack_damage_scale": 1.0, "recovery_rate": 0.3, "capacity_threshold": 60.0},
    {"name": "Gentler damage",  "attack_damage_scale": 0.5, "recovery_rate": 0.5, "capacity_threshold": 50.0},
    {"name": "Harsher damage",  "attack_damage_scale": 1.5, "recovery_rate": 0.2, "capacity_threshold": 70.0},
]

print(f"{'Config':<18}{'Undef. Security':>17}{'Def. Security':>16}{'Undef. QoS':>13}{'Def. QoS':>11}")
print("-" * 75)

for cfg in configs:
    undef = ServiceState(cfg["attack_damage_scale"], cfg["recovery_rate"], cfg["capacity_threshold"])
    for i in range(N):
        undef.apply_flow(bool(y_val[i]), "no_action")
    undef_m = compute_metrics(undef)

    defd = ServiceState(cfg["attack_damage_scale"], cfg["recovery_rate"], cfg["capacity_threshold"])
    for i in range(N):
        defd.apply_flow(bool(y_val[i]), actions[i])
    defd_m = compute_metrics(defd)

    print(f"{cfg['name']:<18}{undef_m['security_pct']:>16.2f}%{defd_m['security_pct']:>15.2f}%"
          f"{undef_m['qos_pct']:>12.2f}%{defd_m['qos_pct']:>10.2f}%")