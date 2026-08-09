# The coordinator. Runs N federated rounds, tolerates node
#       failures via a quorum policy, aggregates with
#       fedbn_average, and gates PROMOTION (not training) through
#       your random-rotating canary check.
# Training and serving are DECOUPLED — every round trains
#       on the newly aggregated candidate regardless of the
#       canary decision. Only "promoted/serving" status depends
#       on passing canary.

import asyncio
import json
import logging
import random
import time

import httpx
import numpy as np

from appcd.models import build_mlp
from appcd.federation import get_batchnorm_indices, fedbn_average
from appcd.serialization import weights_to_json, weights_from_json
from coordinator import config
from coordinator.registry import save_model
from coordinator.dynamodb_writer import write_round_state

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("coordinator")

HEADERS = {"X-APPCD-Token": config.TOKEN}


class State:
    """Everything worth keeping, flushed to disk every round —
    this is what the dashboard will read in a later stage."""
    def __init__(self):
        self.rounds = []
        self.best = {"round": 0, "macro_val": -1.0, "version": 0}
        self.serving_version = 0
        self.deployments = []
        self.node_status = {}

    def flush(self):
        with open(config.STATE_FILE, "w") as f:
            json.dump(self.__dict__, f, indent=2, default=float)


def select_canary_nodes(round_number):
    """Fresh random subset each round, seeded by round_number for
    reproducibility within one run."""
    rng = random.Random(round_number)
    return rng.sample(config.ALL_NODE_IDS, config.CANARY_SIZE)


async def check_health(client):
    print("Checking node health...")
    tasks = [client.get(f"{url}/health", headers=HEADERS,
                        timeout=config.HEALTH_TIMEOUT_S)
             for url in config.NODE_URLS.values()]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    status = {}
    for node_id, result in zip(config.NODE_URLS.keys(), results):
        if isinstance(result, Exception):
            status[node_id] = f"unreachable ({type(result).__name__})"
            print(f"  Node {node_id}: UNREACHABLE ({type(result).__name__})")
        else:
            body = result.json()
            status[node_id] = "ok"
            print(f"  Node {node_id}: OK ({body.get('train_rows')} train rows)")
    return status


async def _round_call(client, node_id, url, payload):
    """NEVER raises — a dead node returns None, round continues without it."""
    start = time.time()
    try:
        resp = await client.post(f"{url}/round", json=payload,
                                 headers=HEADERS,
                                 timeout=config.ROUND_TIMEOUT_S)
        resp.raise_for_status()
        return node_id, resp.json(), time.time() - start
    except Exception as exc:
        log.warning("node %s FAILED this round (%s) — continuing without it",
                   node_id, exc)
        return node_id, None, time.time() - start


async def run_one_round(client, global_weights, round_number):
    payload = {"global_weights": weights_to_json(global_weights)}
    payload_kb = len(json.dumps(payload)) / 1024

    print(f"\nRound {round_number}/{config.N_ROUNDS} — "
          f"training on all nodes ({payload_kb:.0f} KB payload)...")
    tasks = [_round_call(client, node_id, url, payload)
             for node_id, url in config.NODE_URLS.items()]
    results = await asyncio.gather(*tasks)

    reported, latencies = {}, {}
    for node_id, result, elapsed in results:
        latencies[node_id] = round(elapsed, 2)
        if result is not None:
            reported[node_id] = result
            print(f"  Node {node_id}: val accuracy = "
                  f"{result['val_accuracy']:.2f}%  ({elapsed:.1f}s)")

    return reported, latencies, payload_kb

async def evaluate_on_canary(client, weights, canary_nodes, version):
    """
    Evaluates weights on a specific list of canary nodes.
    Now handles BOTH connection failures AND HTTP error status
    codes gracefully — a bad node here degrades the canary
    check rather than crashing the whole federation.
    """
    payload = {"candidate_weights": weights_to_json(weights), "version": version}

    async def _one_check(node_id):
        try:
            resp = await client.post(
                f"{config.NODE_URLS[node_id]}/deploy",
                params={"commit": "false"}, json=payload,
                headers=HEADERS, timeout=config.ROUND_TIMEOUT_S)
            resp.raise_for_status()
            return node_id, resp.json()["val_accuracy"]
        except Exception as exc:
            log.warning("canary check on node %s failed: %s", node_id, exc)
            return node_id, None

    results = await asyncio.gather(*[_one_check(n) for n in canary_nodes])
    accuracies = {node_id: acc for node_id, acc in results if acc is not None}

    if not accuracies:
        return None, {}
    return sum(accuracies.values()) / len(accuracies), accuracies


async def promote_to_all(client, weights, version):
    """Same graceful-failure pattern for the actual promotion fan-out."""
    payload = {"candidate_weights": weights_to_json(weights), "version": version}

    async def _one_promote(node_id, url):
        try:
            resp = await client.post(
                f"{url}/deploy", params={"commit": "true"},
                json=payload, headers=HEADERS,
                timeout=config.ROUND_TIMEOUT_S)
            resp.raise_for_status()
            return node_id, True
        except Exception as exc:
            log.warning("promotion to node %s failed: %s", node_id, exc)
            return node_id, False

    results = await asyncio.gather(
        *[_one_promote(node_id, url) for node_id, url in config.NODE_URLS.items()])
    return [node_id for node_id, ok in results if ok]


async def run_federation():
    state = State()

    print("=" * 60)
    print("APPCD COORDINATOR — Fault-Tolerant Federation + Canary")
    print("=" * 60)
    print(f"Quorum required: {config.MIN_QUORUM}/{len(config.ALL_NODE_IDS)}")
    print(f"Canary size: {config.CANARY_SIZE}, rotating each round")
    print(f"Promotion tolerance: {config.PROMOTION_TOLERANCE_PP}pp\n")

    async with httpx.AsyncClient() as client:

        health = await check_health(client)
        state.node_status = health
        alive = [k for k, v in health.items() if v == "ok"]
        if len(alive) < config.MIN_QUORUM:
            log.error("only %d/%d nodes alive at startup — below quorum, "
                     "aborting", len(alive), len(config.ALL_NODE_IDS))
            state.flush()
            return

        shell = build_mlp(config.N_FEATURES)
        bn_indices = get_batchnorm_indices(shell)
        global_weights = [w.copy() for w in shell.get_weights()]
        serving_weights = [w.copy() for w in global_weights]

        for round_number in range(1, config.N_ROUNDS + 1):

            reported, latencies, payload_kb = await run_one_round(
                client, global_weights, round_number)

            if len(reported) < config.MIN_QUORUM:
                log.error("round %d: only %d/%d nodes reported — below "
                         "quorum %d, DISCARDING round, retrying next",
                         round_number, len(reported),
                         len(config.ALL_NODE_IDS), config.MIN_QUORUM)
                state.rounds.append({
                    "round": round_number, "status": "no_quorum",
                    "reported": list(reported), "latency_s": latencies,
                })
                state.flush()
                continue

            node_weights = [weights_from_json(r["updated_weights"])
                           for r in reported.values()]
            candidate_weights = fedbn_average(node_weights, bn_indices)
            macro_val = float(np.mean(
                [r["val_accuracy"] for r in reported.values()]))

            entry = {
                "round": round_number, "status": "ok",
                "macro_val": round(macro_val, 2),
                "reported": list(reported),
                "missing": [k for k in config.ALL_NODE_IDS if k not in reported],
                "per_node_val": {k: round(r["val_accuracy"], 2)
                                for k, r in reported.items()},
                "latency_s": latencies,
                "payload_kb": round(payload_kb, 1),
            }

            canary_nodes = select_canary_nodes(round_number)
            version = round_number

            old_acc, _ = await evaluate_on_canary(
                client, serving_weights, canary_nodes, version=0)
            new_acc, _ = await evaluate_on_canary(
                client, candidate_weights, canary_nodes, version=version)

            if old_acc is None or new_acc is None:
                decision, reason = "skipped", "canary nodes unreachable"
            else:
                print(f"  Canary {canary_nodes}: "
                      f"serving {old_acc:.2f}% -> candidate {new_acc:.2f}%")
                regression = old_acc - new_acc
                if regression <= config.PROMOTION_TOLERANCE_PP:
                    decision, reason = "promoted", (
                        f"candidate {new_acc:.2f}% vs serving {old_acc:.2f}% "
                        f"within {config.PROMOTION_TOLERANCE_PP}pp")
                else:
                    decision, reason = "rejected", (
                        f"candidate {new_acc:.2f}% regressed "
                        f"{regression:.2f}pp vs serving {old_acc:.2f}%")

            if decision == "promoted":
                ok = await promote_to_all(client, candidate_weights, version)
                serving_weights = [w.copy() for w in candidate_weights]
                state.serving_version = version
                save_model(version, candidate_weights,
                          {"round": round_number, "macro_val": macro_val,
                           "canary_nodes": canary_nodes})
                print(f"  Decision: PROMOTED v{version} to {ok}")
            else:
                print(f"  Decision: {decision.upper()} — {reason}")

            state.deployments.append({
                "version": version, "round": round_number,
                "canary_nodes": canary_nodes,
                "decision": decision, "reason": reason,
            })

            # Training continues regardless of the canary decision —
            # deliberate, see module docstring.
            global_weights = candidate_weights

            if macro_val > state.best["macro_val"]:
                state.best = {"round": round_number,
                             "macro_val": round(macro_val, 2),
                             "version": version}
                entry["new_best"] = True

            print(f"  Macro val: {macro_val:.2f}%   "
                  f"nodes: {''.join(sorted(reported))}   "
                  f"slowest: {max(latencies.values()):.1f}s")

            state.rounds.append(entry)
            write_round_state(entry, state.serving_version)
            state.flush()

    print("\n" + "=" * 60)
    print("FEDERATION COMPLETE")
    print("=" * 60)
    print(f"Best macro val: {state.best['macro_val']:.2f}% "
         f"(round {state.best['round']})")
    print(f"Currently serving: v{state.serving_version}")
    state.flush()


if __name__ == "__main__":
    asyncio.run(run_federation())