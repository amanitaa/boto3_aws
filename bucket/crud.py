from botocore.exceptions import ClientError


def bucket_exists(aws_s3_client, bucket_name) -> bool:
    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/head_bucket.html
    try:
        aws_s3_client.head_bucket(Bucket=bucket_name)
        return True
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code in ("404", "NoSuchBucket"):
            return False
        if code == "403":
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
    response = aws_s3_client.delete_bucket(Bucket=bucket_name)
    status_code = response["ResponseMetadata"]["HTTPStatusCode"]
    if status_code == 204:
        return True
    return False