# Generate OPDS v2.0 JSON from API output
from configparser import ConfigParser
from pathlib import Path

import requests


class SpringerCrawler(object):

    def __init__(self):
        self.config = ConfigParser()
        current_path = Path(__file__).parents[0].resolve()
        config_path = Path(current_path, "config.ini")
        self.config.read(str(config_path))
        self.api_key = self.config["SPRINGER"]["apiKey"]
        self.api_endpoint = "https://api.springernature.com/bookmeta/v1/json"
        self.per_page = 100

    def crawl(self, already_crawled=0):
        total = self.get_springer_total()
        records_retrieved = 0
        remaining = total - already_crawled
        while True:
            try:
                start = remaining - self.per_page
                page_data = self.get_springer_page(start)
                for record in page_data["records"]:
                    yield record
                current_total = int(page_data["result"][0]["total"])
                if current_total != total:
                    difference = current_total - total
                    remaining += difference
                    total = current_total
                records_retrieved += self.per_page
                remaining -= self.per_page
            except Exception as err:
                raise (
                    err,
                    f"Requested {self.per_page} starting at {start} with {total} total records.",
                )
                pass

    def get_springer_page(self, start):
        try:
            params = {
                "q": "sort:date",
                "s": start,
                "p": self.per_page,
                "api_key": self.api_key,
            }
            response = requests.get(self.api_endpoint, params=params)
            response.raise_for_status()
            page_data = response.json()
            return page_data
        except Exception:
            raise

    def get_springer_total(self):
        params = {"q": "sort:date", "s": 1, "p": 1, "api_key": self.api_key}
        response = requests.get(self.api_endpoint, params=params)
        page_data = response.json()
        return int(page_data["result"][0]["total"])
