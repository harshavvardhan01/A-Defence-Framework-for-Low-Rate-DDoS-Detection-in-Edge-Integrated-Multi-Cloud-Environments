# extract_dynamodb_data.py
#
# WHAT: Pulls every round's real, logged data from the
#       appcd-round-state DynamoDB table and prints it in a
#       compact, clean format -- round number, macro validation
#       accuracy, and per-node latency -- suitable for building
#       a genuine convergence curve and computing real latency
#       mean/SD/n, both directly from your actual 30-round
#       AWS deployment run.
#
# WHY:  A raw `aws dynamodb scan` dump is deeply nested JSON
#       with verbose type annotations (each value wrapped as
#       {"N": "97.42"} etc.) -- this script does that
#       unwrapping once, so the output can be pasted directly
#       and used, rather than requiring manual parsing.

import boto3
from decimal import Decimal

TABLE_NAME = "appcd-round-state"
REGION = "eu-west-1"  # matches your coordinator's deployment region

dynamodb = boto3.resource("dynamodb", region_name=REGION)
table = dynamodb.Table(TABLE_NAME)

print("Scanning DynamoDB table for all logged rounds...")
items = []
response = table.scan()
items.extend(response["Items"])

# Handle pagination in case the table has more items than one
# scan page returns (shouldn't matter at 30 rounds, but safe)
while "LastEvaluatedKey" in response:
    response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
    items.extend(response["Items"])

# Sort by round number so output is in chronological order
items.sort(key=lambda x: int(x.get("round_number", x.get("round", 0))))

print(f"\nFound {len(items)} logged rounds.\n")


def to_float(v):
    if isinstance(v, Decimal):
        return float(v)
    return v


print("=" * 90)
print(f"{'Round':<7}{'Macro Val (%)':<16}{'Node A Lat(s)':<15}{'Node B Lat(s)':<15}{'Node D Lat(s)':<15}")
print("=" * 90)

for item in items:
    round_num = item.get("round_number", item.get("round", "?"))
    macro_val = to_float(item.get("macro_val", "N/A"))

    latency = item.get("latency_s", {})
    lat_a = to_float(latency.get("A", "N/A")) if isinstance(latency, dict) else "N/A"
    lat_b = to_float(latency.get("B", "N/A")) if isinstance(latency, dict) else "N/A"
    lat_d = to_float(latency.get("D", "N/A")) if isinstance(latency, dict) else "N/A"

    print(f"{round_num!s:<7}{macro_val!s:<16}{lat_a!s:<15}{lat_b!s:<15}{lat_d!s:<15}")

print("=" * 90)
print("\nCopy the full table above and paste it back — this is exactly")
print("what's needed to build a real convergence curve and compute")
print("real latency mean/SD/n for RQ2.")