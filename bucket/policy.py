import json
import logging

from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def generate_public_read_policy(bucket_name, prefixes=None):
    if prefixes:
        resource = [f"arn:aws:s3:::{bucket_name}/{prefix.strip('/')}/*" for prefix in prefixes]
    else:
        resource = f"arn:aws:s3:::{bucket_name}/*"

    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "PublicReadGetObject",
                "Effect": "Allow",
                "Principal": "*",
                "Action": "s3:GetObject",
                "Resource": resource,
            }
        ],
    }

    return json.dumps(policy)


def allow_public_access(aws_s3_client, bucket_name):
    aws_s3_client.delete_public_access_block(Bucket=bucket_name)
    logger.debug("Public access block removed from '%s'", bucket_name)


def create_bucket_policy(aws_s3_client, bucket_name, policy) -> bool:
    allow_public_access(aws_s3_client, bucket_name)
    response = aws_s3_client.put_bucket_policy(Bucket=bucket_name, Policy=policy)
    status_code = response["ResponseMetadata"]["HTTPStatusCode"]
    if status_code in (200, 204):
        return True
    return False


def read_bucket_policy(aws_s3_client, bucket_name):
    try:
        policy = aws_s3_client.get_bucket_policy(Bucket=bucket_name)
        return policy["Policy"]
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchBucketPolicy":
            return None
        raise
