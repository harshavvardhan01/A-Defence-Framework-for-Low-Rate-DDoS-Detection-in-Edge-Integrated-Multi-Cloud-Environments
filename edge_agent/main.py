# The edge node's complete web service — health check,
#       federated training round, canary/deploy check, and
#       real-time classify-and-respond.
# This is the single, complete file for this node's
#       service. Every endpoint built this term lives here.

import os
import time

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from appcd.federation import NodeTrainer
from appcd.data import get_node_data
from appcd.serialization import weights_to_json, weights_from_json
from appcd.response import decide_action

NODE_ID = os.environ.get("NODE_ID", "A")
N_FEATURES = int(os.environ.get("N_FEATURES", "42"))
TOKEN = os.environ.get("APPCD_TOKEN", "dev-token-change-me")

app = FastAPI(title=f"APPCD Edge Agent \u2014 Node {NODE_ID}")

trainer = NodeTrainer(N_FEATURES)
X_train, y_train, X_val, y_val = get_node_data(NODE_ID, N_FEATURES)

serving = {"version": 0}

print(f"Edge agent starting \u2014 Node {NODE_ID}")
print(f"  Train rows: {X_train.shape[0]}   Val rows: {X_val.shape[0]}")
print(f"  Model parameters: {trainer.model.count_params():,}")


def check_token(x_appcd_token: str = Header(default=None)):
    if x_appcd_token != TOKEN:
        raise HTTPException(status_code=401, detail="bad or missing token")


# ── Request / response schemas ────────────────────────────────

class RoundRequest(BaseModel):
    global_weights: list


class RoundResponse(BaseModel):
    node_id: str
    updated_weights: list
    val_accuracy: float
    val_precision: float
    val_recall: float
    val_fpr: float


class DeployRequest(BaseModel):
    candidate_weights: list
    version: int


class DeployResponse(BaseModel):
    node_id: str
    version: int
    committed: bool
    val_accuracy: float
    val_precision: float
    val_recall: float
    val_fpr: float


class ClassifyRequest(BaseModel):
    features: list


class ClassifyResponse(BaseModel):
    node_id: str
    confidence: float
    action: str
    decision_latency_ms: float


# ── Endpoints ────────────────────────────────────────────────

@app.get("/health")
def health(x_appcd_token: str = Header(default=None)):
    check_token(x_appcd_token)
    return {
        "status": "ok",
        "node_id": NODE_ID,
        "n_features": N_FEATURES,
        "train_rows": int(X_train.shape[0]),
        "val_rows": int(X_val.shape[0]),
        "model_parameters": trainer.model.count_params(),
        "serving_version": serving["version"],
    }


@app.post("/round", response_model=RoundResponse)
def run_round(req: RoundRequest, x_appcd_token: str = Header(default=None)):
    check_token(x_appcd_token)
    global_weights = weights_from_json(req.global_weights)
    updated = trainer.train_round(global_weights, X_train, y_train)
    metrics = trainer.evaluate(X_val, y_val)

    return RoundResponse(
        node_id=NODE_ID,
        updated_weights=weights_to_json(updated),
        val_accuracy=metrics["accuracy"],
        val_precision=metrics["precision"],
        val_recall=metrics["recall"],
        val_fpr=metrics["fpr"],
    )


@app.post("/deploy", response_model=DeployResponse)
def deploy_candidate(req: DeployRequest, commit: bool = False,
                      x_appcd_token: str = Header(default=None)):
    check_token(x_appcd_token)
    candidate_weights = weights_from_json(req.candidate_weights)
    metrics = trainer.evaluate_candidate(candidate_weights, X_val, y_val)

    if commit:
        serving["version"] = req.version

    return DeployResponse(
        node_id=NODE_ID,
        version=req.version,
        committed=commit,
        val_accuracy=metrics["accuracy"],
        val_precision=metrics["precision"],
        val_recall=metrics["recall"],
        val_fpr=metrics["fpr"],
    )


@app.post("/classify", response_model=ClassifyResponse)
def classify(req: ClassifyRequest, x_appcd_token: str = Header(default=None)):
    """
    Simulates real-time detection-and-response: classifies ONE
    flow's features with this node's current model, selects a
    response action, and measures full decision latency \u2014 the
    metric compared against Zhou et al.'s 276.66ms.
    """
    check_token(x_appcd_token)
    import numpy as np

    start = time.perf_counter()

    X = np.array([req.features], dtype=np.float32)
    confidence = float(trainer.model.predict(X, verbose=0)[0][0])
    action = decide_action(confidence)

    elapsed_ms = (time.perf_counter() - start) * 1000

    return ClassifyResponse(
        node_id=NODE_ID,
        confidence=confidence,
        action=action,
        decision_latency_ms=round(elapsed_ms, 3),
    )

@app.get("/export_weights")
def export_weights(x_appcd_token: str = Header(default=None)):
    """Saves this node's current trained model weights to disk,
    for use in fair local comparisons -- exports the SAME model
    object that /round and /deploy already use, unchanged."""
    check_token(x_appcd_token)
    trainer.model.save_weights("federated_model.weights.h5")
    return {"status": "saved", "node_id": NODE_ID}