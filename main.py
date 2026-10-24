import argparse
import sys

from botocore.exceptions import ClientError

from auth import init_client
from bucket.crud import bucket_exists, create_bucket
from bucket.policy import (
    read_bucket_policy,
    public_prefix_policy,
    allow_public_policy,
    assign_policy,
)
from my_args import bucket_arguments

parser = argparse.ArgumentParser(
    description="CLI program that helps with S3 buckets.",
    prog="main.py",
)

subparsers = parser.add_subparsers(dest="command", required=True)

bucket_arguments(subparsers.add_parser("create_bucket", help="Create a bucket if it does not already exist."))
bucket_arguments(subparsers.add_parser("bucket_policy", help="Make /dev and /test public if the bucket has no policy yet.",))


def main():
    args = parser.parse_args()
    s3_client = init_client()

    try:
        match args.command:

            case "create_bucket":
                if bucket_exists(s3_client, args.name):
                    print(f"Bucket: '{args.name}' already exists")
                elif create_bucket(s3_client, args.name):
                    print(f"Bucket: '{args.name}' successfully created")

            case "bucket_policy":
                if read_bucket_policy(s3_client, args.name):
                    print(f"Bucket: '{args.name}' already has a policy")
                else:
                    allow_public_policy(s3_client, args.name)
                    if assign_policy(
                        s3_client, args.name, public_prefix_policy(args.name)
                    ):
                        print(
                            f"Policy assigned: '{args.name}/dev/*' and "
                            f"'{args.name}/test/*' are now public"
                        )

    except ClientError as e:
        print(f"Error: {e.response['Error']['Message']}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
