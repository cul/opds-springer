# Generate OPDS v2.0 JSON from API output
import json
import os
import re
import requests
import sys
from datetime import datetime
from configparser import ConfigParser
from dcps.pickle_utils import unpickle_it

MY_NAME = __file__
MY_PATH = os.path.dirname(__file__)
SCRIPT_NAME = os.path.basename(MY_NAME)
config_path = os.path.join(MY_PATH, "config.ini")
config = ConfigParser()
config.read(config_path)


API_ENDPOINT = 'https://api.springernature.com/bookmeta/v1/json'
API_KEY = config["SPRINGER"]["apiKey"]
ENTITLEMENT_ID = config["API"]["entitlementID"]
PER_PAGE = 100

NOW = datetime.utcnow().strftime(
    "%Y-%m-%dT%H:%M:%S.%fZ")  # Current timestamp in ISO


def page_cache_path(page_number, output_base_dir):
  cache_suffix = ('%06x' % page_number)
  subdir = cache_suffix[-2:]
  cache_dir = os.path.join(output_base_dir, subdir)
  os.makedirs(cache_dir, exist_ok=True)
  cache_name = 'page-%s.json' % cache_suffix
  return os.path.join(cache_dir, cache_name)

def cache_page(page_number, output_base_dir):
    start = (page_number - 1) * PER_PAGE + 1
    out_file = page_cache_path(page_number, output_base_dir)
    url = '%s?q=sort:date&s=%s&p=%s&api_key=%s' % (API_ENDPOINT, str(start), str(PER_PAGE), API_KEY)
    page = springer_get(url)
    with open(out_file, "w") as f:
        json.dump(page, f, indent=2)
    return page

def result(page):
    return page["result"][0]

def count(page):
    return int(result(page)["recordsDisplayed"])

def remaining(page):
    return int(result(page)["total"]) >= (int(result(page)["start"]) + PER_PAGE)


def springer_get(url):
    try:
        print(url)
        initial_page = requests.get(url)
        initial_page.raise_for_status()
    except Exception as err:
        print('*** get_springer_count request error: ' + str(err))
    else:
        return json.loads(initial_page.content)

def get_result_pages(springer_response):
    total = int(result(springer_response)['total'])
    if (0 == total % PER_PAGE):
        return total / PER_PAGE
    else:
        return 1 + total / PER_PAGE

def springer_build_cache(output_base_dir):
    if sys.argv[1]:
        page_ix = int(sys.argv[1])
    else:
        page_ix = 1
    page = cache_page(page_ix, output_base_dir)
    total = count(page)
    expected_pages = get_result_pages(page)
    while remaining(page):
        page_ix = page_ix + 1
        page = cache_page(page_ix, output_base_dir)
        total = total + count(page)

    print("Expected " + str(expected_pages) + " pages.")
    print("Retrieved " + str(page_ix) + " pages.")
    print("Retrieved " + str(total) + " books.")

def main():
    output_base_dir = "output_test/springer/crawl"
    os.makedirs(output_base_dir, exist_ok=True)
    springer_build_cache(output_base_dir)

if __name__ == "__main__":
    main()
