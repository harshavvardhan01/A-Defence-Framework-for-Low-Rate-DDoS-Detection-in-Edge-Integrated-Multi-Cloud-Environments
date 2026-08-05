# coordinator/dynamodb_writer.py
#
# WHAT: Writes one round's summary to the DynamoDB round-state
#       table, as a durable alternative to the local JSON file.
# WHY:  The local state.json is lost if the coordinator's disk
#       is lost. This makes round history durable independent
#       of any single instance -- the production target already
#       named in the Design chapter's control-plane table.
#
# DESIGN NOTE: This is ADDITIVE. state.flush() continues to
# write the local JSON file exactly as before -- this does not
# replace it, only mirrors the SAME entry dict already
# constructed in orchestrator.py, so it can never drift out of
# sync with what the dashboard reads.

import os
import time
import boto3
from decimal import Decimal

DYNAMODB_TABLE = os.environ.get("DYNAMODB_TABLE", "")

_dynamodb = None


def _get_table():
    global _dynamodb
    if not DYNAMODB_TABLE:
        return None
    if _dynamodb is None:
        _dynamodb = boto3.resource("dynamodb")
    return _dynamodb.Table(DYNAMODB_TABLE)


def _to_dynamodb_safe(obj):
    """DynamoDB's boto3 resource API rejects native Python floats
    (requires Decimal) and cannot store empty sets -- this
    recursively converts a normal Python dict (like `entry`)
    into a form DynamoDB will actually accept, without requiring
    orchestrator.py's existing code to change how it builds
    `entry` for the local JSON file."""
    if isinstance(obj, float):
        return Decimal(str(obj))
    if isinstance(obj, dict):
        return {k: _to_dynamodb_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_dynamodb_safe(v) for v in obj]
    return obj


def write_round_state(entry: dict, serving_version: int):
    """
    Mirrors ONE round's entry dict (the same dict orchestrator.py
    already appends to state.rounds and writes to the local JSON
    file) into DynamoDB. Silently no-ops if DYNAMODB_TABLE is not
    set, so this is safe to call unconditionally without breaking
    any deployment that hasn't enabled this feature.
    """
    table = _get_table()
    if table is None:
        return

    try:
        item = _to_dynamodb_safe(dict(entry))
        item["round_number"] = entry["round"]  # matches the table's hash_key
        item["serving_version"] = serving_version
        item["written_at"] = int(time.time())
        table.put_item(Item=item)
    except Exception as e:
        print(f"[WARNING] DynamoDB write failed for round "
              f"{entry.get('round', '?')}: {e}")
        # Deliberately non-fatal: DynamoDB is a durability MIRROR,
        # not a dependency -- the local JSON file (via state.flush())
        # remains the source of truth the rest of the system reads from.