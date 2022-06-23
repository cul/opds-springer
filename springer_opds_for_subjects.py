import json
import os
from datetime import datetime
from math import ceil
from sqlalchemy import *
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import joinedload
from springer import blank_string, config, db_session
from springer.model import SessionManager, Identifier, Edition, Subject, Classification, Contribution, DataSource, get_one_or_create
from springer.subjects.csv_data import generate_subjects
from springer.mappings import opds_language
def opds_images_for(identifier):
    # print or electronic ISBNs will work; sometimes DOI is a little weird and doesn't have the ISBN exactly
    isbn = None
    for alternate_id in identifier.equivalent_identifiers:
        if alternate_id.type == 'ISBN': isbn = alternate_id.identifier
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
def opds_metadata_for(identifier, timestamp):
    metadata = {}
    metadata['identifier'] = "https://dx.doi.org/%s" % (identifier.identifier)
    metadata['modified'] = timestamp.isoformat()
    edition = identifier.editions[0]
    metadata['title'] = edition.title
    metadata['language'] = opds_language(edition.language)
    if (not blank_string(edition.description)): metadata['description'] = edition.description
    metadata['@type'] = "http://schema.org/EBook" # TBD: Map from edition.medium pending migration
    if (edition.publisher): metadata['publisher'] = edition.publisher
    if (edition.published): metadata['published'] = str(edition.published)
    subjects = [ classification.subject.name for classification in identifier.classifications]
    if (subjects != []): metadata['subjects'] = subjects
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

def opds_publication(identifier, timestamp):
    resources = []
    for resource in identifier.resources:
        # TODO/CUL-Lyrasis: what vocabulary do we have to pattern these URLs? Could Springer API key be affilated with SAML IDP?
        resources.append({
            'rel': resource.rel,
            'type': resource.media_type,
            'href': "https://fsso.springer.com/saml/login?idp=urn:mace:incommon:columbia.edu&targetUrl=%s" % (resource.url)
        })
    images = opds_images_for(identifier)
    doc = {
        'metadata': opds_metadata_for(identifier, timestamp)
    }
    if (len(images) > 0): doc['images'] = images
    if (len(resources) > 0): doc['links'] = resources
    return doc

def opds_response_link(page_number, rel):
    return {
        "rel": rel,
        "href": ("https://ebooks-test.library.columbia.edu/static-feeds/springer/springer_test_feed_%s.json" % page_number),
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

def opds_response(page_number, total_pages):
    return {
        "metadata": { "title": "Springer Test Feed" },
        "links": opds_response_links(page_number, total_pages),
        "publications": []
    }
def cache_page(output_base_dir, opds_page, page_number):
    out_file = os.path.join(output_base_dir, ("springer_test_feed_%s.json" % page_number))
    with open(os.path.join(out_file), "w") as f:
        json.dump(opds_page, f, indent=2)

def main():
    output_base_dir = "output_test/springer/opds"
    os.makedirs(output_base_dir, exist_ok=True)

    q = db_session.query(Identifier).join(Classification, Classification.identifier_id == Identifier.id, isouter=True)
    count = q.filter(Identifier.type == 'DOI').filter(Classification.id == None).count()
    total = db_session.query(Identifier).\
        filter(Identifier.type == 'DOI').\
        filter(Identifier.editions.any()).\
        count()
    print("%s identifiers of %s have no subjects" % (str(count), str(total)))
    q = db_session.query(Identifier).\
        filter(Identifier.type == 'DOI').\
        filter(Identifier.editions.any()).\
        filter(Identifier.classifications.any())
    count = q.count()
    print("%s editions of %s have subjects" % (str(count), str(total)))
    load_query = q.options(
        joinedload(Identifier.editions), joinedload(Identifier.classifications).joinedload(Classification.subject)
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
        response = opds_response(page_number, total_pages)
        for identifier in identifiers_page:
            response['publications'].append(opds_publication(identifier, timestamp))
        cache_page(output_base_dir, response, page_number)
        offset += page_size
        print("cached page %s of %s" % (str(page_number), str(total_pages)))
if __name__ == "__main__":
    main()
