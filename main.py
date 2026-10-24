import argparse
import json
import logging
import sys
from urllib.error import URLError

from botocore.exceptions import ClientError, NoCredentialsError

from auth import init_client
from bucket.crud import list_buckets, create_bucket, delete_bucket, bucket_exists
from bucket.lifecycle import set_lifecycle_policy, read_lifecycle_policy
from bucket.versioning import versioning, get_versioning_status
from bucket.organize import object_per_extension
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
    upload_small_file,
    upload_large_file,
    object_exists,
    delete_object,
    UnsupportedFileType,
)
from object.policy import set_object_access_policy
from object.versioning import list_object_versions, promote_previous_version
from object.type_folder import upload_to_type_folder

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

        case "upload":
            require_bucket(s3_client, args.name)
            url = upload_to_type_folder(s3_client, args.name, args.file, args.overwrite)
            logger.info("Uploaded: %s", url)

        case "upload_small":
            require_bucket(s3_client, args.name)
            url = upload_small_file(
                s3_client, args.name, args.file, args.key, not args.skip_mime_check
            )
            logger.info("Uploaded: %s", url)

        case "upload_large":
            require_bucket(s3_client, args.name)
            if args.chunk_mb < 5:
                parser.error("--chunk_mb must be at least 5 (S3 minimum part size)")
            url = upload_large_file(
                s3_client,
                args.name,
                args.file,
                args.key,
                not args.skip_mime_check,
                args.chunk_mb,
            )
            logger.info("Uploaded: %s", url)

        case "set_lifecycle":
            require_bucket(s3_client, args.name)
            if args.days < 1:
                parser.error("--days must be at least 1")
            if set_lifecycle_policy(s3_client, args.name, args.days):
                logger.info(
                    "Lifecycle policy set: objects in '%s' are deleted %d days after creation",
                    args.name,
                    args.days,
                )

        case "read_lifecycle":
            require_bucket(s3_client, args.name)
            rules = read_lifecycle_policy(s3_client, args.name)
            if rules:
                print(json.dumps(rules, indent=2))
            else:
                logger.info("Bucket '%s' has no lifecycle policy", args.name)

        case "bucket" if args.organize:
            require_bucket(s3_client, args.name)
            moved = object_per_extension(s3_client, args.name)
            if not moved:
                logger.info("Nothing to organize in '%s'", args.name)
            else:
                logger.info("Moved %d file(s) in '%s':", sum(moved.values()), args.name)
                for folder, count in sorted(moved.items()):
                    print(f"{folder} - {count}")

        case "versioning":
            require_bucket(s3_client, args.name)
            if args.status:
                status = get_versioning_status(s3_client, args.name)
                if status == "Enabled":
                    logger.info("Versioning is enabled for '%s'", args.name)
                elif status == "Suspended":
                    logger.info("Versioning is suspended for '%s'", args.name)
                else:
                    logger.info("Versioning has never been enabled for '%s'", args.name)
            else:
                versioning(s3_client, args.name, args.enable)
                logger.info(
                    "Versioning %s for '%s'",
                    "enabled" if args.enable else "suspended",
                    args.name,
                )

        case "object" if args.list_versions:
            require_bucket(s3_client, args.name)
            versions = list_object_versions(s3_client, args.name, args.key)
            if not versions:
                logger.info("File '%s' does not exist in '%s'", args.key, args.name)
            else:
                logger.info("File '%s' has %d version(s):", args.key, len(versions))
                for number, version in enumerate(versions, start=1):
                    print(
                        f"  {number}. {version['LastModified']:%Y-%m-%d %H:%M:%S %Z}"
                        f"  {version['Size']} bytes  id={version['VersionId']}"
                        f"{'  (latest)' if version['IsLatest'] else ''}"
                    )

        case "object" if args.promote_previous:
            require_bucket(s3_client, args.name)
            previous, new_version_id = promote_previous_version(
                s3_client, args.name, args.key
            )
            logger.info(
                "Version from %s of '%s' promoted to the newest version (id=%s)",
                f"{previous['LastModified']:%Y-%m-%d %H:%M:%S}",
                args.key,
                new_version_id,
            )

        case "object":
            require_bucket(s3_client, args.name)
            if not object_exists(s3_client, args.name, args.key):
                logger.info("File '%s' does not exist in '%s'", args.key, args.name)
            else:
                result = delete_object(s3_client, args.name, args.key)
                if result["deleted"]:
                    logger.info("File '%s' deleted from '%s'", args.key, args.name)
                if result["delete_marker"]:
                    logger.info(
                        "Versioning is enabled: older versions of '%s' are kept",
                        args.key,
                    )

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
    except (FileNotFoundError, FileExistsError, ValueError) as e:
        logger.error(e)
        sys.exit(1)
    except NoCredentialsError:
        logger.error("AWS credentials not found. Copy .env.example to .env and fill it in.")
        sys.exit(1)
    except ClientError as e:
        logger.error(e.response["Error"]["Message"])
        sys.exit(1)
