import logging

from bucket.policy import allow_public_access

logger = logging.getLogger(__name__)


def set_object_access_policy(aws_s3_client, bucket_name, file_name) -> bool:
    allow_public_access(aws_s3_client, bucket_name)
    aws_s3_client.put_bucket_ownership_controls(
        Bucket=bucket_name,
        OwnershipControls={"Rules": [{"ObjectOwnership": "BucketOwnerPreferred"}]},
    )
    logger.debug("ACLs enabled on '%s'", bucket_name)

    response = aws_s3_client.put_object_acl(
        ACL="public-read", Bucket=bucket_name, Key=file_name
    )
    status_code = response["ResponseMetadata"]["HTTPStatusCode"]
    if status_code == 200:
        return True
    return False
