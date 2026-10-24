import boto3
from os import getenv
from dotenv import load_dotenv

load_dotenv()


def init_client():
    client = boto3.client(
        "s3",
        aws_access_key_id=getenv("aws_access_key_id"),
        aws_secret_access_key=getenv("aws_secret_access_key"),
        aws_session_token=getenv("aws_session_token"),
        region_name=getenv("aws_region_name"),
    )
    return client
