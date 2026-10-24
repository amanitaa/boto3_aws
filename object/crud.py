import io
import logging
import tempfile
from hashlib import md5
from time import time
from urllib.request import Request, urlopen

import magic

logger = logging.getLogger(__name__)

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
        mime_type = magic.from_file(tmp.name, mime=True)
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


def list_objects(aws_s3_client, bucket_name) -> list:
    return aws_s3_client.list_objects_v2(Bucket=bucket_name).get("Contents", [])
