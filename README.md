# AWS BTU - boto3

# S3 CLI

S3 CLI tool, created for educational purposes. Built with **Poetry**, **boto3**,
**python-dotenv**, **logging**, **argparse** and **python-magic**.

## Install

`python-magic` needs the `libmagic` system library:

```shell
brew install libmagic          # macOS
sudo apt install libmagic1     # Ubuntu / Debian
```

Then install the project and add your credentials:

```shell
poetry install
cp .env.example .env   # fill in AWS Learner Lab credentials
```

## Usage

Run the help command to see all commands (`-h` or `--help`). Every command also
has its own help, e.g. `main.py upload_url -h`.

```shell
poetry run python main.py -h
```

Add `-v` before the command to see debug logs:

```shell
poetry run python main.py -v list_buckets
```

## Bucket

### List buckets

```shell
poetry run python main.py list_buckets
```

### Create bucket

Checks whether the bucket exists; if it does not, creates it.

```shell
poetry run python main.py create_bucket "any-name-of-s3"
```

### Check if bucket exists

```shell
poetry run python main.py bucket_exists "any-name-of-s3"
```

### Delete bucket

Checks whether the bucket exists; if it does, deletes all of its objects
(including old versions) and then the bucket itself. Otherwise prints that the
bucket does not exist.

```shell
poetry run python main.py delete_bucket "any-name-of-s3"
```

## Policy

### Read bucket policy

```shell
poetry run python main.py read_policy "any-name-of-s3"
```

### Create bucket policy

Checks whether the bucket has a policy; if it does not, assigns a public read
policy. By default the whole bucket becomes public; use `-p` to only make
specific folders public.

```shell
poetry run python main.py create_policy "any-name-of-s3"
poetry run python main.py create_policy "any-name-of-s3" -p dev test
```

> New buckets have **Block Public Access** enabled, which rejects public
> policies with `AccessDenied`. The command removes it with
> `delete_public_access_block` before assigning the policy.

## Object

### Download a file from a URL and upload it

Only `.bmp`, `.jpg`, `.jpeg`, `.png`, `.webp` and `.mp4` files are accepted.
The type is detected from the file **content** with `python-magic`, not from
the URL, so a text file renamed to `.jpg` is rejected. The uploaded object gets
the correct extension and `Content-Type`.

```shell
poetry run python main.py upload_url "any-name-of-s3" https://upload.wikimedia.org/wikipedia/commons/a/a9/Example.jpg
```

Options:

- `-k`, `--keep_local` – also save the file locally
- `--public` – make the uploaded file public

### Make an object public

```shell
poetry run python main.py public_object "any-name-of-s3" "file_name.jpg"
```

> New buckets have ACLs disabled (`BucketOwnerEnforced`), so `put_object_acl`
> fails with `AccessControlListNotSupported`. The command removes the public
> access block and switches object ownership to `BucketOwnerPreferred` first.

### List objects

```shell
poetry run python main.py list_objects "any-name-of-s3"
```

## Project structure

| File | Functions |
|---|---|
| `auth.py` | `init_client()` |
| `bucket/crud.py` | `list_buckets()`, `create_bucket()`, `delete_bucket()`, `bucket_exists()` |
| `bucket/policy.py` | `generate_public_read_policy()`, `create_bucket_policy()`, `read_bucket_policy()` |
| `object/crud.py` | `download_file_and_upload_to_s3()` |
| `object/policy.py` | `set_object_access_policy()` |
| `my_args.py` | CLI arguments |
| `main.py` | Entry point |
