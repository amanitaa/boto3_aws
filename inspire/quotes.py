import json
from typing import Optional
from urllib.parse import quote as url_quote
from urllib.request import Request, urlopen

API_URL = "https://api.quotable.kurokeita.dev/api/quotes/random"
HEADERS = {
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36",
}


def get_quote(author: Optional[str] = None) -> dict:
    url = f"{API_URL}?author={url_quote(author)}" if author else API_URL

    with urlopen(Request(url, headers=HEADERS), timeout=15) as response:
        result = json.loads(response.read().decode())

    # The API answers 200 with {} when it has no quote for the author.
    if not result:
        raise ValueError(f"The API has no quotes by '{author}'" if author else "The API returned no quote")
    return result


def print_quote(result: dict):
    print(result["quote"]["content"])
    print("---")
    print(result["quote"]["author"]["name"])


def save_quote(aws_s3_client, bucket_name, result: dict) -> str:
    quote = result["quote"]
    key = f"quotes/{quote['author']['slug']}-{quote['id']}.json"
    aws_s3_client.put_object(
        Bucket=bucket_name,
        Key=key,
        Body=json.dumps(result, indent=2, ensure_ascii=False).encode(),
        ContentType="application/json",
    )
    return key
