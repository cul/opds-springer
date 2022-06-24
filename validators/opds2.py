import glob
import json
import logging
import os
import re
import requests
import sys

from webpub_manifest_parser.core import ManifestParser, ManifestParserResult
from webpub_manifest_parser.opds2 import OPDS2FeedParserFactory

def stream_manifest(stream_id, encoding="utf-8"):
    url_pattern = re.compile('^https?://*', re.IGNORECASE)
    if (url_pattern.match(stream_id)):
        response = requests.get(stream_id, stream=True)
        return response.raw
    else:
        return open(stream_id, "r", encoding="utf-8")

def parsing_errors(manifest_stream, log_level=logging.WARNING):
    # logging.root.level = logging.DEBUG
    logging.getLogger("webpub_manifest_parser.opds2").level = log_level

    parser_factory = OPDS2FeedParserFactory()
    parser = parser_factory.create()

    return parser.parse_stream(manifest_stream).errors

def validate(stream_id, encoding="utf-8", log_level=logging.WARNING):
    try:
        return len(parsing_errors(stream_manifest(stream_id, encoding), log_level)) == 0
    except:
        print(sys.exc_info())
        return False

def main():
    path_arg = sys.argv[1]
    file_paths = []
    if os.path.isfile(path_arg): file_paths = [path_arg]
    if (os.path.isdir(path_arg)): file_paths = glob.glob(os.path.join(path_arg, '*.json'))
    for file_path in file_paths:
        with open(file_path) as f:
            doc = json.load(f)
            no_links = [pub for pub in doc['publications'] if (not 'links' in pub)]
            if (len(no_links) > 0):
                print("validation errors %s - publications without links" % (file_path))
                print(no_links)
                quit()
        if not validate(file_path, log_level=logging.WARNING):
            print("validation errors %s" % (file_path))
            quit()

if __name__ == "__main__":
    main()
