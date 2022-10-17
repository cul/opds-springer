import json
import os
from datetime import datetime
from math import ceil
import urllib.parse
from sqlalchemy import *
from sqlalchemy.orm import joinedload
from springer import blank_string, config, db_session
from springer.model import SessionManager, Edition, Subject, Classification, Contribution, get_one_or_create, NONFICTION_CLASSIFIER
from springer.subjects.csv_data import generate_subjects
from springer.mappings import palace_language

def opds_images_for(edition):
    # print or electronic ISBNs will work; sometimes DOI is a little weird and doesn't have the ISBN exactly
    isbn = edition.print_isbn or edition.e_isbn
    return [] if isbn == None else [
        {
            "href": ("https://covers.springernature.com/books/jpg_height_648_pixels/%s.jpg" % isbn),
            "type": "image/jpeg"
        },
        {
            "href": ("https://covers.springernature.com/books/jpg_width_125_pixels/%s.jpg" % isbn),
            "width": 125,
            "type": "image/jpeg"
        },
        {
            "href": ("https://covers.springernature.com/books/jpg_width_95_pixels/%s.jpg" % isbn),
            "width": 95,
            "type": "image/jpeg"
        }
    ]
def opds_metadata_for(edition, timestamp):
    metadata = {}
    metadata['identifier'] = "urn:" + edition.primary_identifier
    metadata['modified'] = timestamp.isoformat()
    metadata['title'] = edition.title
    metadata['language'] = palace_language(edition.language)
    if (not blank_string(edition.description)): metadata['description'] = edition.description
    metadata['@type'] = "http://schema.org/EBook" # TBD: Map from edition.medium pending migration
    if (edition.publisher): metadata['publisher'] = edition.publisher
    if (edition.published): metadata['published'] = str(edition.published)
    subjects = [ classification.subject.name for classification in edition.classifications]
    subjects.insert(0, NONFICTION_CLASSIFIER)
    metadata['subject'] = subjects
    authors = []
    editors = []
    for contribution in edition.contributions:
        if contribution.role == 'Primary Author':
            authors.insert(0, {'name': contribution.contributor.name})
        if contribution.role == 'Author':
            authors.append({'name': contribution.contributor.name})
        if contribution.role == 'Editor':
            editors.append({'name': contribution.contributor.name})
    if (len(authors) > 0): metadata['author'] = authors
    if (len(editors) > 0): metadata['editor'] = editors
    return metadata

def opds_publication(edition, timestamp):
    resources = []
    for resource in edition.resources:
        # TODO: Debug Springer epub URLs
        if resource.media_type == 'application/epub+zip': continue
        resourceUrl = resource.url.replace('http:', 'https:', 1)
        # TODO/CUL-Lyrasis: what vocabulary do we have to pattern these URLs? Could Springer API key be affilated with SAML IDP?
        resources.append({
            'rel': 'http://opds-spec.org/acquisition/open-access', # resource.rel,
            'type': resource.media_type,
            # https://sp.springer.com/saml/login?idp=urn%3Amace%3Aincommon%3Acolumbia.edu&targetUrl=http%3A%2F%2Flink.springer.com
            'href': ("https://sp.springer.com/saml/login?idp={}&targetUrl={}".format("urn%3Amace%3Aincommon%3Acolumbia.edu", urllib.parse.quote(resourceUrl)))
        })
    images = opds_images_for(edition)
    doc = {
        'metadata': opds_metadata_for(edition, timestamp)
    }
    if (len(images) > 0): doc['images'] = images
    if (len(resources) > 0): doc['links'] = resources
    return doc

def opds_response_link(page_number, rel):
    return {
        "rel": rel,
        "href": ("https://ebooks.library.columbia.edu/springer/opds.json?page=%s" % page_number),
        "type": "application/opds+json"
    }

def opds_response_links(page_number, total_pages):
    links = []
    self_rel = "self"
    first_rel = "first"
    last_rel = "last"
    prev_rel = "prev"
    next_rel = "next"
    if page_number == 1:
        self_rel = ["self", "first"]
        first_rel = None
        prev_rel = None
    if page_number == 2:
        first_rel = ["prev", "first"]
        prev_rel = None
    if (page_number + 1 == total_pages):
        last_rel = ["next", "last"]
        next_rel = None
    if (page_number == total_pages):
        self_rel = ["self", "last"]
        next_rel = None
        last_rel = None
    if self_rel:
        links.append(opds_response_link(page_number, self_rel))
    if first_rel:
        links.append(opds_response_link(1, first_rel))
    if last_rel:
        links.append(opds_response_link(total_pages, last_rel))
    if next_rel:
        links.append(opds_response_link(page_number + 1, next_rel))
    if prev_rel:
        links.append(opds_response_link(page_number - 1, prev_rel))
    return links

def opds_response(page_number, count, page_size):
    total_pages = ceil(count/page_size)
    return {
        "metadata": {
            "title": "Springer PDF Feed",
            "itemsPerPage": page_size,
            "currentPage": page_number,
            "numberOfItems": count
        },
        "links": opds_response_links(page_number, total_pages),
        "publications": []
    }
def cache_page(output_base_dir, opds_page, page_number):
    out_file = os.path.join(output_base_dir, ("springer_feed_%s.json" % page_number))
    with open(os.path.join(out_file), "w") as f:
        json.dump(opds_page, f, indent=2)

def main():
    output_base_dir = "output_prod/springer/opds"
    os.makedirs(output_base_dir, exist_ok=True)

    q = db_session.query(Edition).join(Classification, Classification.edition_id == Edition.id, isouter=True)
    count = q.filter(Classification.id == None).count()
    total = db_session.query(Edition).\
        count()
    print("%s identifiers of %s have no subjects" % (str(count), str(total)))
    q = db_session.query(Edition).\
        filter(Edition.classifications.any()).\
        filter(Edition.resources.any())
    count = q.count()
    print("%s editions of %s have subjects and resources" % (str(count), str(total)))
    load_query = q.options(
        joinedload(Edition.classifications).joinedload(Classification.subject)
    )
    timestamp = datetime.utcnow()
    page_size = 1000
    total_pages = ceil(count/page_size)
    print("%s editions yield %s pages" % (str(count), str(total_pages)))
    load_query = load_query.limit(page_size)
    offset = 0
    while offset < count:
        page_number = int((offset / page_size) + 1)
        identifiers_page = load_query.offset(offset).all()
        response = opds_response(page_number, count, page_size)
        for identifier in identifiers_page:
            response['publications'].append(opds_publication(identifier, timestamp))
        cache_page(output_base_dir, response, page_number)
        offset += page_size
        print("cached page %s of %s" % (str(page_number), str(total_pages)))
if __name__ == "__main__":
    main()
