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
poetry run python main.py "any-name-of-s3"
```
