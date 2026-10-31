def bucket_arguments(parser):
    parser.add_argument(
        "name",
        type=str,
        help="Pass bucket name.",
    )
    return parser


def build_subcommands(subparsers):
    subparsers.add_parser("list_buckets", help="List all buckets.")

    bucket_arguments(
        subparsers.add_parser(
            "create_bucket", help="Create a bucket if it does not already exist."
        )
    )
    bucket_arguments(
        subparsers.add_parser(
            "delete_bucket", help="Delete a bucket (and its contents) if it exists."
        )
    )
    bucket_arguments(
        subparsers.add_parser("bucket_exists", help="Check if a bucket exists.")
    )
    bucket_arguments(
        subparsers.add_parser("read_policy", help="Print the bucket policy.")
    )

    create_policy = bucket_arguments(
        subparsers.add_parser(
            "create_policy",
            help="Assign a public read policy if the bucket has no policy yet.",
        )
    )
    create_policy.add_argument(
        "-p",
        "--prefix",
        nargs="+",
        metavar="PREFIX",
        help="Only make these folders public, e.g. -p dev test. "
        "Default: the whole bucket.",
    )

    upload = bucket_arguments(
        subparsers.add_parser(
            "upload_url",
            help="Download a file from a URL and upload it to the bucket "
            "(only .bmp, .jpg, .jpeg, .png, .webp, .mp4).",
        )
    )
    upload.add_argument("url", type=str, help="Link to the file.")
    upload.add_argument(
        "-k", "--keep_local", action="store_true", help="Also save the file locally."
    )
    upload.add_argument(
        "--public", action="store_true", help="Make the uploaded file public."
    )

    object_acl = bucket_arguments(
        subparsers.add_parser("public_object", help="Make one object public.")
    )
    object_acl.add_argument("key", type=str, help="Object key (file name).")

    bucket_arguments(
        subparsers.add_parser("list_objects", help="List objects in a bucket.")
    )

    obj = bucket_arguments(
        subparsers.add_parser(
            "object", help="Work with one object: delete it or manage its versions."
        )
    )
    obj.add_argument("key", type=str, help="Object key (file name), e.g. dev/photo.png.")
    obj_action = obj.add_mutually_exclusive_group(required=True)
    obj_action.add_argument(
        "-del", "--delete", action="store_true", help="Delete the object from the bucket."
    )
    obj_action.add_argument(
        "-lv",
        "--list_versions",
        action="store_true",
        help="Show how many versions the object has and when each was created.",
    )
    obj_action.add_argument(
        "-pv",
        "--promote_previous",
        action="store_true",
        help="Copy the second-to-last version so it becomes the newest version.",
    )

    bucket = bucket_arguments(
        subparsers.add_parser("bucket", help="Work with a whole bucket, e.g. organize it (-org).")
    )
    bucket_action = bucket.add_mutually_exclusive_group(required=True)
    bucket_action.add_argument(
        "-org",
        "--organize",
        action="store_true",
        help="Move each top-level file into a folder named after its extension.",
    )

    old_versions = bucket_arguments(
        subparsers.add_parser(
            "delete_old_versions",
            help="Delete versions of the given files that are older than 6 months.",
        )
    )
    old_versions.add_argument(
        "files", nargs="+", metavar="file", help="One or more object keys (file names)."
    )
    old_versions.add_argument(
        "-m", "--months", type=int, default=6, help="Age limit in months. Default: 6."
    )
    old_versions.add_argument(
        "--include_latest",
        action="store_true",
        help="Also delete the current version if it is too old (deletes the file).",
    )
    old_versions.add_argument(
        "--dry_run", action="store_true", help="Only show what would be deleted."
    )

    host = bucket_arguments(
        subparsers.add_parser(
            "host", help="Host a static website (a folder or index.html) on S3."
        )
    )
    host.add_argument(
        "-s",
        "--source",
        type=str,
        required=True,
        help="Folder with index.html (e.g. react_app/dist) or an index.html file.",
    )
    host.add_argument(
        "--spa",
        action="store_true",
        help="Single-page app (React): serve index.html for unknown paths.",
    )
    host.add_argument(
        "--clean",
        action="store_true",
        help="Delete files in the bucket that are not part of this upload.",
    )

    bucket_arguments(
        subparsers.add_parser("unhost", help="Turn off static website hosting.")
    )

    bucket_versioning = bucket_arguments(
        subparsers.add_parser("versioning", help="Show, enable or suspend bucket versioning.")
    )
    versioning_action = bucket_versioning.add_mutually_exclusive_group(required=True)
    versioning_action.add_argument(
        "-st", "--status", action="store_true", help="Show whether versioning is enabled."
    )
    versioning_action.add_argument(
        "-on", "--enable", action="store_true", help="Enable versioning."
    )
    versioning_action.add_argument(
        "-off", "--suspend", action="store_true", help="Suspend versioning."
    )

    upload = bucket_arguments(
        subparsers.add_parser(
            "upload",
            help="Upload a file of any type into a folder named after its real type "
            "(detected with python-magic).",
        )
    )
    upload.add_argument("file", type=str, help="Path to the local file.")
    upload.add_argument(
        "--overwrite", action="store_true", help="Replace the file if it already exists."
    )

    for command, help_text in (
        ("upload_small", "Upload a small local file (up to 100 MB) with a single request."),
        ("upload_large", "Upload a large local file in parts (multipart upload)."),
    ):
        upload_local = bucket_arguments(subparsers.add_parser(command, help=help_text))
        upload_local.add_argument("file", type=str, help="Path to the local file.")
        upload_local.add_argument(
            "-k", "--key", type=str, help="Object key in S3. Default: the file name."
        )
        upload_local.add_argument(
            "--skip_mime_check",
            action="store_true",
            help="Allow any file type (by default only .bmp, .jpg, .jpeg, .png, .webp, .mp4).",
        )
        if command == "upload_large":
            upload_local.add_argument(
                "--chunk_mb",
                type=int,
                default=8,
                help="Part size in MB (minimum 5). Default: 8.",
            )

    lifecycle = bucket_arguments(
        subparsers.add_parser(
            "set_lifecycle",
            help="Delete objects automatically N days after creation (default 120).",
        )
    )
    lifecycle.add_argument(
        "-d", "--days", type=int, default=120, help="Days until deletion. Default: 120."
    )

    bucket_arguments(
        subparsers.add_parser("read_lifecycle", help="Print the bucket lifecycle rules.")
    )
