import argparse
import sys

from botocore.exceptions import ClientError

from auth import init_client
from bucket.crud import bucket_exists, create_bucket
from my_args import bucket_arguments

parser = argparse.ArgumentParser(
    description="Create an S3 bucket if it does not already exist.",
    prog="main.py",
)
bucket_arguments(parser)


def main():
    s3_client = init_client()
    args = parser.parse_args()

    try:
        if bucket_exists(s3_client, args.name):
            print(f"Bucket: '{args.name}' already exists")
        elif create_bucket(s3_client, args.name):
            print(f"Bucket: '{args.name}' successfully created")
    except ClientError as e:
        print(f"Error: {e.response['Error']['Message']}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
