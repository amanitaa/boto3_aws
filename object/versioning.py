import calendar
import logging
from datetime import datetime, timezone

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


def months_ago(months, now=None) -> datetime:
    now = now or datetime.now(timezone.utc)
    month_index = now.year * 12 + now.month - 1 - months
    year, month = divmod(month_index, 12)
    day = min(now.day, calendar.monthrange(year, month + 1)[1])
    return now.replace(year=year, month=month + 1, day=day)


def delete_versions_older_than(
    aws_s3_client, bucket_name, file_name, cutoff, include_latest=False, dry_run=False
) -> tuple:
    versions = list_object_versions(aws_s3_client, bucket_name, file_name)
    old = [
        v
        for v in versions
        if v["LastModified"] < cutoff and (include_latest or not v["IsLatest"])
    ]

    if old and not dry_run:
        for start in range(0, len(old), 1000):
            batch = old[start : start + 1000]
            response = aws_s3_client.delete_objects(
                Bucket=bucket_name,
                Delete={
                    "Objects": [
                        {"Key": file_name, "VersionId": v["VersionId"]} for v in batch
                    ],
                    "Quiet": True,
                },
            )
            for error in response.get("Errors", []):
                logger.error(
                    "Could not delete version %s of '%s': %s",
                    error["VersionId"],
                    file_name,
                    error["Message"],
                )

    return versions, old
