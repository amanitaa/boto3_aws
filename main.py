import argparse
import json
import logging
import sys
from urllib.error import URLError

from botocore.exceptions import ClientError, NoCredentialsError

from auth import init_client
from bucket.crud import list_buckets, create_bucket, delete_bucket, bucket_exists
from bucket.policy import (
    read_bucket_policy,
    generate_public_read_policy,
    create_bucket_policy,
)
from my_args import build_subcommands
from object.crud import (
    download_file_and_upload_to_s3,
    list_objects,
    public_url,
    UnsupportedFileType,
)
from object.policy import set_object_access_policy

logger = logging.getLogger("s3_cli")


parser = argparse.ArgumentParser(
    description="CLI program that helps with S3 buckets.",
    prog="main.py",
    epilog="Run 'main.py <command> -h' to see help for a command.",
)
parser.add_argument(
    "-v", "--verbose", action="store_true", help="Show debug logs."
)

subparsers = parser.add_subparsers(dest="command", required=True, title="commands", metavar="<command>")
build_subcommands(subparsers)


def require_bucket(s3_client, bucket_name):
    if not bucket_exists(s3_client, bucket_name):
        logger.error("Bucket '%s' does not exist", bucket_name)
        sys.exit(1)


def main():
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )
    for name in ("boto3", "botocore", "s3transfer", "urllib3"):
        logging.getLogger(name).setLevel(logging.WARNING)

    s3_client = init_client()

    match args.command:

        case "list_buckets":
            buckets = list_buckets(s3_client)
            if not buckets:
                logger.info("No buckets found")
            for bucket in buckets:
                print(f"  {bucket['Name']}  (created {bucket['CreationDate']:%Y-%m-%d})")

        case "create_bucket":
            if bucket_exists(s3_client, args.name):
                logger.info("Bucket '%s' already exists", args.name)
            elif create_bucket(s3_client, args.name):
                logger.info("Bucket '%s' successfully created", args.name)

        case "delete_bucket":
            if not bucket_exists(s3_client, args.name):
                logger.info("Bucket '%s' does not exist", args.name)
            elif delete_bucket(s3_client, args.name):
                logger.info("Bucket '%s' successfully deleted", args.name)

        case "bucket_exists":
            exists = bucket_exists(s3_client, args.name)
            logger.info("Bucket '%s' %s", args.name, "exists" if exists else "does not exist")

        case "read_policy":
            require_bucket(s3_client, args.name)
            policy = read_bucket_policy(s3_client, args.name)
            if policy:
                print(json.dumps(json.loads(policy), indent=2))
            else:
                logger.info("Bucket '%s' has no policy", args.name)

        case "create_policy":
            require_bucket(s3_client, args.name)
            if read_bucket_policy(s3_client, args.name):
                logger.info("Bucket '%s' already has a policy", args.name)
            else:
                policy = generate_public_read_policy(args.name, args.prefix)
                if create_bucket_policy(s3_client, args.name, policy):
                    targets = ", ".join(f"{p}/" for p in args.prefix) if args.prefix else "all files"
                    logger.info("Policy assigned: %s in '%s' are now public", targets, args.name)

        case "upload_url":
            require_bucket(s3_client, args.name)
            url = download_file_and_upload_to_s3(
                s3_client, args.name, args.url, args.keep_local
            )
            logger.info("Uploaded: %s", url)
            if args.public and set_object_access_policy(
                s3_client, args.name, url.rsplit("/", 1)[-1]
            ):
                logger.info("File is now public")

        case "public_object":
            require_bucket(s3_client, args.name)
            if set_object_access_policy(s3_client, args.name, args.key):
                logger.info("Object is public: %s", public_url(s3_client, args.name, args.key))

        case "list_objects":
            require_bucket(s3_client, args.name)
            objects = list_objects(s3_client, args.name)
            if not objects:
                logger.info("Bucket '%s' is empty", args.name)
            for obj in objects:
                print(f"  {obj['Key']}  ({obj['Size']} bytes)")


if __name__ == "__main__":
    try:
        main()
    except UnsupportedFileType as e:
        logger.error(e)
        sys.exit(1)
    except URLError as e:
        logger.error("Could not download file: %s", e.reason)
        sys.exit(1)
    except NoCredentialsError:
        logger.error("AWS credentials not found. Copy .env.example to .env and fill it in.")
        sys.exit(1)
    except ClientError as e:
        logger.error(e.response["Error"]["Message"])
        sys.exit(1)
