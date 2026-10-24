import logging

logger = logging.getLogger(__name__)


def list_object_versions(aws_s3_client, bucket_name, file_name) -> list:
    versions = []
    paginator = aws_s3_client.get_paginator("list_object_versions")
    for page in paginator.paginate(Bucket=bucket_name, Prefix=file_name):
        for version in page.get("Versions", []):
            if version["Key"] == file_name:
                versions.append(version)

    versions.sort(key=lambda v: v["LastModified"], reverse=True)
    return versions


def rollback_to_version(aws_s3_client, bucket_name, file_name, version) -> str:
    response = aws_s3_client.copy_object(
        Bucket=bucket_name,
        Key=file_name,
        CopySource={"Bucket": bucket_name, "Key": file_name, "VersionId": version},
    )
    return response.get("VersionId")


def promote_previous_version(aws_s3_client, bucket_name, file_name) -> tuple:
    versions = list_object_versions(aws_s3_client, bucket_name, file_name)
    if len(versions) < 2:
        raise ValueError(
            f"'{file_name}' has {len(versions)} version(s); "
            "at least 2 are needed to promote the previous one"
        )

    previous = versions[1]
    logger.debug("Promoting version %s of '%s'", previous["VersionId"], file_name)
    new_version_id = rollback_to_version(
        aws_s3_client, bucket_name, file_name, previous["VersionId"]
    )
    return previous, new_version_id
