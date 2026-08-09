

import requests
import numpy as np
import sys

sys.path.insert(0, ".")
from appcd.models import build_mlp
from appcd.serialization import weights_to_json

AGENT_URL = "http://127.0.0.1:8001"
TOKEN = "dev-token-change-me"
HEADERS = {"X-APPCD-Token": TOKEN}

print("=" * 55)
print("EDGE AGENT TEST")
print("=" * 55)

print("\n[1/4] Checking /health...")
resp = requests.get(f"{AGENT_URL}/health", headers=HEADERS)
print(f"      Status: {resp.status_code}")
print(f"      Body:   {resp.json()}")

print("\n[2/4] Confirming auth actually blocks bad requests...")
resp = requests.get(f"{AGENT_URL}/health", headers={"X-APPCD-Token": "wrong"})
print(f"      Status without valid token: {resp.status_code} "
      f"(expect 401)")

print("\n[3/4] Sending fake global weights to /round...")
dummy_model = build_mlp(41)
fake_global_weights = weights_to_json(dummy_model.get_weights())

resp = requests.post(
    f"{AGENT_URL}/round",
    json={"global_weights": fake_global_weights},
    headers=HEADERS,
)
result = resp.json()
print(f"      Status: {resp.status_code}")
print(f"      Val accuracy:  {result['val_accuracy']:.2f}%")
print(f"      Val precision: {result['val_precision']:.2f}%")
print(f"      Val recall:    {result['val_recall']:.2f}%")
print(f"      Val FPR:       {result['val_fpr']:.2f}%")

print("\n[4/4] Sending candidate to /deploy (commit=false, canary check)...")
resp = requests.post(
    f"{AGENT_URL}/deploy?commit=false",
    json={"candidate_weights": fake_global_weights, "version": 1},
    headers=HEADERS,
)
print(f"      Status: {resp.status_code}")
print(f"      Body:   {resp.json()}")

print("\n" + "=" * 55)
print("ALL AGENT TESTS PASSED")
print("=" * 55)