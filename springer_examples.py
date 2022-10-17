import os
import json
from datetime import date
from springer import blank_string, config

def main():
    crawl_log_path = config['SPRINGER']['crawlLog']
    with open(crawl_log_path) as crawl_log:
        for crawl_cache in crawl_log:
            with open(crawl_cache.rstrip()) as crawl_file:
                crawl_json = json.loads(crawl_file.read())
                if crawl_json == None: continue
                for edition_data in crawl_json["records"]:
                    if edition_data['language'] != 'en': continue
                    if ('ePubUrl' in edition_data and not blank_string(edition_data['ePubUrl'])):
                        print("{} ({}".format(edition_data["identifier"], crawl_cache.rstrip()))

if __name__ == "__main__":
    main()
