import logging

from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def set_lifecycle_policy(aws_s3_client, bucket_name, days=120) -> bool:
    response = aws_s3_client.put_bucket_lifecycle_configuration(
        Bucket=bucket_name,
        LifecycleConfiguration={
            "Rules": [
                {
                    "ID": f"delete-objects-after-{days}-days",
                    "Filter": {"Prefix": ""},
                    "Status": "Enabled",
                    "Expiration": {"Days": days},
                    "NoncurrentVersionExpiration": {"NoncurrentDays": days},
                    "AbortIncompleteMultipartUpload": {"DaysAfterInitiation": 7},
                }
            ]
        },
    )
    status_code = response["ResponseMetadata"]["HTTPStatusCode"]
    if status_code == 200:
        return True
    return False


def read_lifecycle_policy(aws_s3_client, bucket_name):
    try:
        response = aws_s3_client.get_bucket_lifecycle_configuration(Bucket=bucket_name)
        return response["Rules"]
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchLifecycleConfiguration":
            return None
        raise
