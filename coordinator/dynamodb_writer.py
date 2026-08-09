# Writes one round's summary to the DynamoDB round-state
#       table, as a durable alternative to the local JSON file.
#The local state.json is lost if the coordinator's disk
#       is lost. This makes round history durable independent
#       of any single instance
#

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

    if isinstance(obj, float):
        return Decimal(str(obj))
    if isinstance(obj, dict):
        return {k: _to_dynamodb_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_dynamodb_safe(v) for v in obj]
    return obj


def write_round_state(entry: dict, serving_version: int):

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
        