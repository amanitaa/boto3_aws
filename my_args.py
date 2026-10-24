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
