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

### Organize files by extension

Moves every top-level file into a folder named after its extension and prints
how many files were moved per extension.

```shell
poetry run python main.py bucket "any-name-of-s3" -org
```

```
INFO: Moved 6 file(s) in 'any-name-of-s3':
csv - 4
jpg - 1
unknown - 1
```

- `image.jpg` → `jpg/image.jpg`, `users.csv` → `csv/users.csv`
- Extensions are lower-cased (`photo.PNG` → `png/photo.PNG`); files without an
  extension go to `unknown/`
- Only top-level files are moved, so files already in a folder (e.g.
  `dev/photo.png`) stay where they are and running it again is safe
- If the target already exists, the file is skipped with a warning instead of
  being overwritten

> S3 has no real folders: a "folder" is just a key prefix, so moving a file
> means copying it to `jpg/image.jpg` and deleting `image.jpg`.

### Versioning

Show whether versioning is enabled (`-st`), or enable (`-on`) / suspend
(`-off`) it.

```shell
poetry run python main.py versioning "any-name-of-s3" -st
poetry run python main.py versioning "any-name-of-s3" -on
poetry run python main.py versioning "any-name-of-s3" -off
```

### Lifecycle policy

Deletes objects automatically 120 days after they were created (use `-d` to
change the number of days). The rule also removes old object versions and
cleans up unfinished multipart uploads after 7 days.

```shell
poetry run python main.py set_lifecycle "any-name-of-s3"
poetry run python main.py set_lifecycle "any-name-of-s3" -d 30
poetry run python main.py read_lifecycle "any-name-of-s3"
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

### Upload a small file

Uploads a local file (up to 100 MB) with a single `put_object` request.

```shell
poetry run python main.py upload_small "any-name-of-s3" ./photo.png
poetry run python main.py upload_small "any-name-of-s3" ./photo.png -k dev/photo.png
```

### Upload a large file

Uploads a local file in parts with a **multipart upload** (`upload_file` +
`TransferConfig`): the file is split into 8 MB parts that are uploaded in
parallel, and a progress bar is shown. Use `--chunk_mb` to change the part size
(S3 minimum is 5 MB).

```shell
poetry run python main.py upload_large "any-name-of-s3" ./video.mp4
poetry run python main.py upload_large "any-name-of-s3" ./video.mp4 --chunk_mb 16
```

Options for both upload commands:

- `-k`, `--key` – object key in S3 (default: the file name)
- `--skip_mime_check` – allow any file type; by default only `.bmp`, `.jpg`,
  `.jpeg`, `.png`, `.webp` and `.mp4` are accepted (checked with `python-magic`)

### Delete a file

Pass the bucket name, the file name (key) and the `-del` flag. If the file does
not exist, the command says so instead of failing.

```shell
poetry run python main.py object "any-name-of-s3" "dev/photo.png" -del
```

> If versioning is enabled on the bucket, S3 only adds a *delete marker*: the
> file disappears from listings, but older versions are kept.

### File versions

Show how many versions a file has, with the creation date of each (newest
first):

```shell
poetry run python main.py object "any-name-of-s3" "notes.txt" -lv
```

Promote the second-to-last version to a new version. It is copied with
`copy_object`, so the history is kept and the restored content becomes the
newest version:

```shell
poetry run python main.py object "any-name-of-s3" "notes.txt" -pv
```

> Versioning must be enabled on the bucket, and the file needs at least 2
> versions.

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
| `bucket/lifecycle.py` | `set_lifecycle_policy()`, `read_lifecycle_policy()` |
| `bucket/organize.py` | `object_per_extension()` |
| `bucket/versioning.py` | `versioning()`, `get_versioning_status()` |
| `bucket/policy.py` | `generate_public_read_policy()`, `create_bucket_policy()`, `read_bucket_policy()` |
| `object/crud.py` | `download_file_and_upload_to_s3()`, `upload_small_file()`, `upload_large_file()`, `delete_object()` |
| `object/versioning.py` | `list_object_versions()`, `rollback_to_version()`, `promote_previous_version()` |
| `object/policy.py` | `set_object_access_policy()` |
| `my_args.py` | CLI arguments |
| `main.py` | Entry point |
