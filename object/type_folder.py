import logging
import mimetypes
import os

import magic

from object.crud import UploadProgress, object_exists, public_url

logger = logging.getLogger(__name__)

GENERIC_MIME_TYPES = {"text/plain", "application/octet-stream", "inode/x-empty"}
NO_EXTENSION_FOLDER = "unknown"


def magic_extensions(file_path) -> list:
    try:
        found = magic.Magic(extension=True).from_file(file_path)
    except (NotImplementedError, magic.MagicException):
        return []
    return [] if found == "???" else found.split("/")


def folder_for_file(file_path) -> tuple:
    mime_type = magic.from_file(file_path, mime=True)
    own_extension = os.path.splitext(file_path)[1].lstrip(".").lower()

    if mime_type in GENERIC_MIME_TYPES:
        if own_extension:
            return own_extension, mime_type
        return ("txt" if mime_type.startswith("text/") else NO_EXTENSION_FOLDER), mime_type

    valid_extensions = magic_extensions(file_path) + [
        ext.lstrip(".") for ext in mimetypes.guess_all_extensions(mime_type, strict=False)
    ]
    if own_extension in valid_extensions:
        return own_extension, mime_type

    guessed = mimetypes.guess_extension(mime_type, strict=False)
    folder = guessed.lstrip(".") if guessed else (valid_extensions or [None])[0]
    folder = folder or own_extension or NO_EXTENSION_FOLDER

    if own_extension:
        logger.warning(
            "File name says '.%s' but the content is %s, using folder '%s/'",
            own_extension,
            mime_type,
            folder,
        )
    return folder, mime_type


def upload_to_type_folder(aws_s3_client, bucket_name, file_path, overwrite=False) -> str:
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    folder, mime_type = folder_for_file(file_path)
    logger.info("Detected file type: %s -> folder '%s/'", mime_type, folder)
    if mime_type in GENERIC_MIME_TYPES:
        mime_type = mimetypes.guess_type(file_path)[0] or mime_type

    key = f"{folder}/{os.path.basename(file_path)}"
    if not overwrite and object_exists(aws_s3_client, bucket_name, key):
        raise FileExistsError(
            f"'{key}' already exists in '{bucket_name}'. Use --overwrite to replace it."
        )

    progress = UploadProgress(os.path.getsize(file_path))
    aws_s3_client.upload_file(
        file_path,
        bucket_name,
        key,
        ExtraArgs={"ContentType": mime_type},
        Callback=progress,
    )
    progress.finish()

    return public_url(aws_s3_client, bucket_name, key)
