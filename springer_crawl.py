# Generate OPDS v2.0 JSON from API output
from configparser import ConfigParser
from datetime import datetime
from pathlib import Path

import requests

config = ConfigParser()
current_path = Path(__file__).parents[0].resolve()
config_path = Path(current_path, "config.ini")
config.read(str(config_path))


API_ENDPOINT = "https://api.springernature.com/bookmeta/v1/json"
API_KEY = config["SPRINGER"]["apiKey"]
PER_PAGE = 100

NOW = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")  # Current timestamp in ISO


def crawl_springer(already_crawled=0):
    total = get_springer_total()
    records_retrieved = 0
    remaining = total - already_crawled
    while True:
        try:
            start = remaining - PER_PAGE
            page_data = get_springer_page(start, PER_PAGE)
            for record in page_data["records"]:
                yield record
            current_total = int(page_data["result"][0]["total"])
            if current_total != total:
                difference = current_total - total
                remaining += difference
                total = current_total
            records_retrieved += PER_PAGE
            remaining -= PER_PAGE
        except Exception as err:
            raise (
                err,
                "Requested {PER_PAGE} starting at {start} with {total} total records.",
            )
            pass


def get_springer_page(start, per_page):
    try:
        params = {"q": "sort:date", "s": start, "p": per_page, "api_key": API_KEY}
        response = requests.get(API_ENDPOINT, params=params)
        response.raise_for_status()
        page_data = response.json()
        return page_data
    except Exception:
        raise


def get_springer_total():
    params = {"q": "sort:date", "s": 1, "p": 1, "api_key": API_KEY}
    response = requests.get(API_ENDPOINT, params=params)
    page_data = response.json()
    return int(page_data["result"][0]["total"])


def main():
    crawl_springer()


if __name__ == "__main__":
    main()
