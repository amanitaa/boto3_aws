import io
import logging
import os
import sys
import tempfile
from hashlib import md5
from time import time
from urllib.request import Request, urlopen

import magic
from botocore.exceptions import ClientError
from boto3.s3.transfer import TransferConfig

logger = logging.getLogger(__name__)

MB = 1024 * 1024
SMALL_FILE_LIMIT = 100 * MB

ALLOWED_MIME_TYPES = {
    "image/bmp": ".bmp",
    "image/x-ms-bmp": ".bmp",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "video/mp4": ".mp4",
}


class UnsupportedFileType(Exception):
    pass


def detect_file_type(content) -> tuple:
    with tempfile.NamedTemporaryFile() as tmp:
        tmp.write(content)
        tmp.flush()
        return detect_file_type_from_path(tmp.name)


def detect_file_type_from_path(file_path) -> tuple:
    mime_type = magic.from_file(file_path, mime=True)
    if mime_type not in ALLOWED_MIME_TYPES:
        raise UnsupportedFileType(
            f"File type '{mime_type}' is not allowed. "
            "Allowed formats: .bmp, .jpg, .jpeg, .png, .webp, .mp4"
        )
    return mime_type, ALLOWED_MIME_TYPES[mime_type]


def public_url(aws_s3_client, bucket_name, file_name) -> str:
    region = aws_s3_client.meta.region_name
    return f"https://{bucket_name}.s3.{region}.amazonaws.com/{file_name}"


def download_file_and_upload_to_s3(
    aws_s3_client, bucket_name, url, keep_local=False
) -> str:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request) as response:
        content = response.read()
    logger.debug("Downloaded %d bytes from %s", len(content), url)

    mime_type, extension = detect_file_type(content)
    logger.info("Detected file type: %s", mime_type)

    file_name = f"file_{md5(str(time()).encode('utf-8')).hexdigest()}{extension}"
    aws_s3_client.upload_fileobj(
        Fileobj=io.BytesIO(content),
        Bucket=bucket_name,
        ExtraArgs={"ContentType": mime_type},
        Key=file_name,
    )

    if keep_local:
        with open(file_name, mode="wb") as local_file:
            local_file.write(content)
        logger.info("Saved local copy: %s", file_name)

    return public_url(aws_s3_client, bucket_name, file_name)


def prepare_local_upload(file_path, key, validate_type) -> tuple:
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    extra_args = {}
    if validate_type:
        mime_type, _ = detect_file_type_from_path(file_path)
        logger.info("Detected file type: %s", mime_type)
        extra_args["ContentType"] = mime_type
    else:
        extra_args["ContentType"] = magic.from_file(file_path, mime=True)

    return key or os.path.basename(file_path), extra_args


def upload_small_file(
    aws_s3_client, bucket_name, file_path, key=None, validate_type=True
) -> str:
    size = os.path.getsize(file_path) if os.path.isfile(file_path) else 0
    if size > SMALL_FILE_LIMIT:
        raise ValueError(
            f"File is {size / MB:.1f} MB; small uploads are limited to "
            f"{SMALL_FILE_LIMIT // MB} MB. Use upload_large instead."
        )
    key, extra_args = prepare_local_upload(file_path, key, validate_type)

    with open(file_path, "rb") as file:
        aws_s3_client.put_object(Bucket=bucket_name, Key=key, Body=file, **extra_args)
    logger.debug("put_object: %s (%d bytes)", key, size)

    return public_url(aws_s3_client, bucket_name, key)


def upload_large_file(
    aws_s3_client, bucket_name, file_path, key=None, validate_type=True, chunk_mb=8
) -> str:
    key, extra_args = prepare_local_upload(file_path, key, validate_type)
    size = os.path.getsize(file_path)

    config = TransferConfig(
        multipart_threshold=chunk_mb * MB,
        multipart_chunksize=chunk_mb * MB,
        max_concurrency=10,
        use_threads=True,
    )
    progress = UploadProgress(size)
    aws_s3_client.upload_file(
        file_path,
        bucket_name,
        key,
        ExtraArgs=extra_args,
        Config=config,
        Callback=progress,
    )
    progress.finish()

    return public_url(aws_s3_client, bucket_name, key)


class UploadProgress:
    def __init__(self, total):
        self.total = total
        self.sent = 0
        self.last_percent = -1

    def __call__(self, bytes_sent):
        self.sent += bytes_sent
        percent = int(self.sent * 100 / self.total) if self.total else 100
        if percent != self.last_percent and sys.stderr.isatty():
            self.last_percent = percent
            print(
                f"\r  uploading: {percent:3d}% ({self.sent / MB:.1f}/{self.total / MB:.1f} MB)",
                end="",
                file=sys.stderr,
                flush=True,
            )

    def finish(self):
        if sys.stderr.isatty():
            print(file=sys.stderr, flush=True)


def list_objects(aws_s3_client, bucket_name) -> list:
    return aws_s3_client.list_objects_v2(Bucket=bucket_name).get("Contents", [])


def object_exists(aws_s3_client, bucket_name, key) -> bool:
    try:
        aws_s3_client.head_object(Bucket=bucket_name, Key=key)
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] in ("404", "NoSuchKey"):
            return False
        raise


def delete_object(aws_s3_client, bucket_name, key) -> dict:
    response = aws_s3_client.delete_object(Bucket=bucket_name, Key=key)
    status_code = response["ResponseMetadata"]["HTTPStatusCode"]
    return {
        "deleted": status_code == 204,
        "delete_marker": response.get("DeleteMarker", False),
    }
