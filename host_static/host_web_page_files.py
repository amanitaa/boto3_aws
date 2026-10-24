import logging
import mimetypes
from pathlib import Path

import magic

logger = logging.getLogger(__name__)

mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("text/javascript", ".mjs")
mimetypes.add_type("image/svg+xml", ".svg")
mimetypes.add_type("application/manifest+json", ".webmanifest")


def content_type_for(file_path) -> str:
    content_type = mimetypes.guess_type(file_path.name)[0]
    if content_type:
        return content_type
    return magic.from_file(str(file_path), mime=True)


def static_web_page_file(aws_s3_client, bucket_name, path) -> list:
    root = Path(path).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"Not found: {path}")

    files = [root] if root.is_file() else sorted(p for p in root.rglob("*") if p.is_file())
    base = root.parent if root.is_file() else root
    if not any(f.relative_to(base).as_posix() == "index.html" for f in files):
        raise ValueError(f"'{path}' has no index.html at its top level")

    uploaded = []
    for file_path in files:
        key = file_path.relative_to(base).as_posix()
        extra_args = {"ContentType": content_type_for(file_path)}
        if file_path.suffix == ".html":
            extra_args["CacheControl"] = "no-cache"

        aws_s3_client.upload_file(str(file_path), bucket_name, key, ExtraArgs=extra_args)
        logger.info("Uploaded %-40s %s", key, extra_args["ContentType"])
        uploaded.append(key)

    return uploaded


def delete_other_files(aws_s3_client, bucket_name, keep) -> int:
    keep = set(keep)
    stale = []
    paginator = aws_s3_client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket_name):
        stale.extend(item["Key"] for item in page.get("Contents", []) if item["Key"] not in keep)

    for start in range(0, len(stale), 1000):
        aws_s3_client.delete_objects(
            Bucket=bucket_name,
            Delete={"Objects": [{"Key": key} for key in stale[start : start + 1000]], "Quiet": True},
        )
    return len(stale)
