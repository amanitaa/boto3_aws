from botocore.exceptions import ClientError

# Older regions use "s3-website-<region>", all others use "s3-website.<region>".
DASH_ENDPOINT_REGIONS = {
    "us-east-1",
    "us-west-1",
    "us-west-2",
    "ap-southeast-1",
    "ap-southeast-2",
    "ap-northeast-1",
    "eu-west-1",
    "sa-east-1",
    "us-gov-west-1",
}


def set_bucket_website_policy(aws_s3_client, bucket_name, switch, error_document=None) -> bool:
    if not switch:
        response = aws_s3_client.delete_bucket_website(Bucket=bucket_name)
        return response["ResponseMetadata"]["HTTPStatusCode"] == 204

    website_configuration = {"IndexDocument": {"Suffix": "index.html"}}
    if error_document:
        website_configuration["ErrorDocument"] = {"Key": error_document}

    response = aws_s3_client.put_bucket_website(
        Bucket=bucket_name, WebsiteConfiguration=website_configuration
    )
    return response["ResponseMetadata"]["HTTPStatusCode"] == 200


def get_website_configuration(aws_s3_client, bucket_name):
    try:
        return aws_s3_client.get_bucket_website(Bucket=bucket_name)
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchWebsiteConfiguration":
            return None
        raise


def website_url(aws_s3_client, bucket_name) -> str:
    region = aws_s3_client.meta.region_name
    separator = "-" if region in DASH_ENDPOINT_REGIONS else "."
    return f"http://{bucket_name}.s3-website{separator}{region}.amazonaws.com"
