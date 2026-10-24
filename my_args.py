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
