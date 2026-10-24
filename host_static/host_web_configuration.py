from botocore.exceptions import ClientError


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
    return f"http://{bucket_name}.s3-website-{region}.amazonaws.com"
