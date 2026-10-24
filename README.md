# AWS BTU - boto3

# S3 CLI

S3 CLI tool, created for educational purposes. Check `.env.example` to see the credentials the script needs.

## Install

```shell
poetry install
cp .env.example .env   # fill in AWS Learner Lab credentials
```

## Usage

Run the help command to see the available CLI options (`-h` or `--help`):

```shell
poetry run python main.py -h
```

## Bucket

### Create bucket

Checks whether the bucket exists; if it does not, creates it.

```shell
poetry run python main.py create_bucket "any-name-of-s3"
```

### Bucket policy

Checks whether the bucket has a policy; if it does not, assigns one that makes
all files under `dev/` and `test/` publicly readable.

```shell
poetry run python main.py bucket_policy "any-name-of-s3"
```

> New buckets have **Block Public Access** enabled, which rejects public
> policies with `AccessDenied`. The command turns off `BlockPublicPolicy` and
> `RestrictPublicBuckets` for the bucket before assigning the policy.
