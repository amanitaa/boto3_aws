def bucket_arguments(parser):
    parser.add_argument(
        "name",
        type=str,
        help="Pass bucket name.",
    )
    return parser
