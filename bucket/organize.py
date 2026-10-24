import logging
import os
from collections import Counter

logger = logging.getLogger(__name__)

NO_EXTENSION_FOLDER = "unknown"


def extension_folder(key) -> str:
    extension = os.path.splitext(key)[1].lstrip(".").lower()
    return extension or NO_EXTENSION_FOLDER


def object_per_extension(aws_s3_client, bucket_name) -> Counter:
    keys = []
    paginator = aws_s3_client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket_name):
        keys.extend(item["Key"] for item in page.get("Contents", []))
    existing = set(keys)

    moved = Counter()
    for key in keys:
        if "/" in key:
            continue

        folder = extension_folder(key)
        new_key = f"{folder}/{key}"
        if new_key in existing:
            logger.warning("Skipped '%s': '%s' already exists", key, new_key)
            continue

        aws_s3_client.copy(
            CopySource={"Bucket": bucket_name, "Key": key},
            Bucket=bucket_name,
            Key=new_key,
        )
        aws_s3_client.delete_object(Bucket=bucket_name, Key=key)
        logger.debug("Moved '%s' -> '%s'", key, new_key)
        moved[folder] += 1

    return moved
