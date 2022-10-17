import os
import csv
import json
import hashlib
from datetime import date
from springer import blank_string, config
from springer.mappings import palace_language
from springer.model import (
    SessionManager, Genre, EditionGenre, Classification, Contribution, Contributor,
    Edition, Resource, create, get_one_or_create
)
from springer.subjects.csv_data import get_subjects_dict

def pairtree_for(identifier, output_base_dir):
    md5 = hashlib.md5()
    md5.update(identifier.encode('UTF-8'))
    hash_value = md5.hexdigest()
    cache_dir = os.path.join(output_base_dir, hash_value[0:2], hash_value[2:4])
    os.makedirs(cache_dir, exist_ok=True)
    cache_suffix = identifier[len('doi:10.1007/'):len(identifier)]
    cache_name = '%s.json' % cache_suffix
    return os.path.join(cache_dir, cache_name)

def main():
    num_identifiers = 0
    crawl_log_path = config['SPRINGER']['crawlLog']
    api_cache_path = config['SPRINGER']['apiCache']
    md5 = hashlib.md5()
    csv_path = config['CSV']['springerSubjects']
    subjects = dict()
    with open(csv_path, newline='') as csvfile:
        csv_reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        subjects = get_subjects_dict(csv_reader)
    with open(crawl_log_path) as crawl_log:
        for crawl_cache in crawl_log:
            with open(crawl_cache.rstrip()) as crawl_file:
                crawl_json = json.loads(crawl_file.read())
                if crawl_json == None: continue
                for edition_data in crawl_json["records"]:
                    doi = edition_data['identifier']
                    subjects_key = doi[4:len(doi)]
                    if subjects_key in subjects:
                        out_path = pairtree_for(doi, api_cache_path)
                        subject_values = [subject for subject in subjects[subjects_key] if not blank_string(subject)]

                        subject_facets = [{"value": subject_value, "count" : "1" } for subject_value in subject_values]
                        api_response = {
                            "apiMessage": "This JSON was provided by Springer Nature",
                            "query": "sort:date&" + doi,
                            "apiKey": config['SPRINGER']['apiCache'],
                            "result": [
                                {
                                    "total": "1",
                                    "start": "1",
                                    "pageLength": "1",
                                    "recordsDisplayed": "1"
                                }
                            ],
                            "records": [ edition_data ],
                            "facets": [
                                {
                                    "name": "subject",
                                    "values": subject_facets
                                },
                                {
                                    "name": "type",
                                    "values": [
                                        {
                                            "value": "Book",
                                            "count": "1"
                                        }
                                    ]
                                }
                            ]
                        }
                        with open(out_path, "w") as f:
                            json.dump(api_response, f, indent=2)
                            num_identifiers += 1

    print("%s API records split out" % (str(num_identifiers)))

if __name__ == "__main__":
    main()
