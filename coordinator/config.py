# All coordinator settings, overridable via environment
#       variables.
#  When this moves to Docker/AWS, every value here gets
#       supplied differently per deployment (real IPs instead of
#       localhost) without touching any code.

import os


ACTIVE_NODES = os.environ.get("ACTIVE_NODES", "A,B,C,D").split(",")

NODE_URLS = {
    node_id: url for node_id, url in {
        "A": os.environ.get("AGENT_A", "http://127.0.0.1:8001"),
        "B": os.environ.get("AGENT_B", "http://127.0.0.1:8002"),
        "C": os.environ.get("AGENT_C", "http://127.0.0.1:8003"),
        "D": os.environ.get("AGENT_D", "http://127.0.0.1:8004"),
    }.items() if node_id in ACTIVE_NODES
}
ALL_NODE_IDS = list(NODE_URLS.keys())

TOKEN = os.environ.get("APPCD_TOKEN", "dev-token-change-me")
N_FEATURES = int(os.environ.get("N_FEATURES", "41"))

N_ROUNDS = int(os.environ.get("ROUNDS", "5"))
ROUND_TIMEOUT_S = float(os.environ.get("ROUND_TIMEOUT_S", "60"))
HEALTH_TIMEOUT_S = float(os.environ.get("HEALTH_TIMEOUT_S", "10"))


MIN_QUORUM = int(os.environ.get("MIN_QUORUM", "3"))

# Canary policy — rotating random subset design.
CANARY_SIZE = int(os.environ.get("CANARY_SIZE", "2"))
PROMOTION_TOLERANCE_PP = float(os.environ.get("PROMOTION_TOLERANCE_PP", "2.0"))

REGISTRY_DIR = os.environ.get("REGISTRY_DIR", "registry")
S3_BUCKET = os.environ.get("S3_BUCKET", "")   
DYNAMODB_TABLE = os.environ.get("DYNAMODB_TABLE", "")
STATE_FILE = os.environ.get("STATE_FILE", "state.json")