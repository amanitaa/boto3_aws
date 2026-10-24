import json

from botocore.exceptions import ClientError


def public_prefix_policy(bucket_name, prefixes=("dev", "test")):
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "PublicReadDevTest",
                "Effect": "Allow",
                "Principal": "*",
                "Action": "s3:GetObject",
                "Resource": [
                    f"arn:aws:s3:::{bucket_name}/{prefix}/*" for prefix in prefixes
                ],
            }
        ],
    }

    return json.dumps(policy)


def read_bucket_policy(aws_s3_client, bucket_name):
    try:
        policy = aws_s3_client.get_bucket_policy(Bucket=bucket_name)
        return policy["Policy"]
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchBucketPolicy":
            return None
        raise


def allow_public_policy(aws_s3_client, bucket_name):
    aws_s3_client.put_public_access_block(
        Bucket=bucket_name,
        PublicAccessBlockConfiguration={
            "BlockPublicAcls": True,
            "IgnorePublicAcls": True,
            "BlockPublicPolicy": False,
            "RestrictPublicBuckets": False,
        },
    )


def assign_policy(aws_s3_client, bucket_name, policy) -> bool:
    response = aws_s3_client.put_bucket_policy(Bucket=bucket_name, Policy=policy)
    status_code = response["ResponseMetadata"]["HTTPStatusCode"]
    if status_code in (200, 204):
        return True
    return False
