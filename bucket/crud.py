import logging

from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def list_buckets(aws_s3_client) -> list:
    return aws_s3_client.list_buckets()["Buckets"]


def bucket_exists(aws_s3_client, bucket_name) -> bool:
    try:
        aws_s3_client.head_bucket(Bucket=bucket_name)
        return True
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code in ("404", "NoSuchBucket"):
            return False
        if code == "403":
            logger.debug("Bucket %s exists but belongs to another account", bucket_name)
            return True
        raise


def create_bucket(aws_s3_client, bucket_name) -> bool:
    region = aws_s3_client.meta.region_name
    if region == "us-east-1":
        response = aws_s3_client.create_bucket(Bucket=bucket_name)
    else:
        response = aws_s3_client.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={"LocationConstraint": region},
        )
    status_code = response["ResponseMetadata"]["HTTPStatusCode"]
    if status_code == 200:
        return True
    return False


def empty_bucket(aws_s3_client, bucket_name) -> int:
    deleted = 0
    paginator = aws_s3_client.get_paginator("list_object_versions")
    for page in paginator.paginate(Bucket=bucket_name):
        objects = [
            {"Key": item["Key"], "VersionId": item["VersionId"]}
            for item in page.get("Versions", []) + page.get("DeleteMarkers", [])
        ]
        if objects:
            aws_s3_client.delete_objects(
                Bucket=bucket_name, Delete={"Objects": objects, "Quiet": True}
            )
            deleted += len(objects)
    return deleted


def delete_bucket(aws_s3_client, bucket_name) -> bool:
    deleted = empty_bucket(aws_s3_client, bucket_name)
    if deleted:
        logger.info("Deleted %d object(s) from '%s'", deleted, bucket_name)
    response = aws_s3_client.delete_bucket(Bucket=bucket_name)
    status_code = response["ResponseMetadata"]["HTTPStatusCode"]
    if status_code == 204:
        return True
    return False
