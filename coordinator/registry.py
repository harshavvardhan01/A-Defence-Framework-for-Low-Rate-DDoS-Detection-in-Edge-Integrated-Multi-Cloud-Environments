# Saves every promoted model as a versioned artefact.
# A registry is what makes rollback and audit possible

import json
import logging
import os

import numpy as np

from coordinator import config

log = logging.getLogger("registry")


def save_model(version, weights, meta):
    os.makedirs(config.REGISTRY_DIR, exist_ok=True)
    path = os.path.join(config.REGISTRY_DIR, f"model-v{version}.npz")
    np.savez_compressed(path, *weights)

    meta_path = os.path.join(config.REGISTRY_DIR, f"model-v{version}.json")
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    size_kb = os.path.getsize(path) / 1024
    log.info("registry: saved model v%s locally (%.0f KB)", version, size_kb)

    if config.S3_BUCKET:
        try:
            import boto3
            s3 = boto3.client("s3")
            s3.upload_file(path, config.S3_BUCKET,
                           f"models/model-v{version}.npz")
            s3.put_object(Bucket=config.S3_BUCKET,
                          Key=f"models/model-v{version}.json",
                          Body=json.dumps(meta, indent=2))
            log.info("registry: mirrored v%s to s3://%s",
                     version, config.S3_BUCKET)
        except Exception:
            log.exception("registry: S3 upload failed — continuing local-only")

    return path