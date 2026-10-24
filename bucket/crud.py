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
