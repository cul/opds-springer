import os
import json
import hashlib
import csv
from datetime import date
from springer import blank_string, blank_value, config, db_session
from springer.mappings import palace_language
from springer.model import (
    SessionManager, Genre, EditionGenre, Classification, Contribution, Contributor,
    Edition, Resource, Subject, create, get_one_or_create
)
from sqlalchemy import *
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm.exc import NoResultFound

def edition_for_identifier(identifier):
    q = db_session.query(Edition).filter_by(primary_identifier=identifier)

    try:
        return q.one()
    except NoResultFound:
        return None

def stub_edition(identifier):
    return create(db_session, Edition, primary_identifier=identifier)

def contributor_for_name(name):
    find_with=dict(name=name)
    create_with = dict()
    (contributor, new) = get_one_or_create(
        db_session, Contributor, create_method_kwargs=create_with, **find_with
    )
    return contributor

def update_edition(api_identifier, edition, kbart_data, api_data):
    # pull primary_identifier (doi) from title_id
    # KBART data
    # publication_title print_identifier    online_identifier   date_first_issue_online num_first_vol_online    num_first_issue_online  date_last_issue_online  num_last_vol_online num_last_issue_online   title_url   first_author    title_id    embargo_info    coverage_depth  coverage_notes  publisher_name  publication_type    date_monograph_published_print  date_monograph_published_online monograph_volume    monograph_edition   first_editor    parent_publication_title_id preceding_publication_title_id  access_type
    ## pull title from publication_title
    if (('publication_title' in kbart_data) and (not blank_string(kbart_data['publication_title']))):
        edition.title = kbart_data['publication_title']
    ## pull publisher from publisher_name
    edition.publisher = kbart_data['publisher_name']
    ## pull print_isbn from print_identifier
    edition.print_isbn = kbart_data['print_identifier']
    ## pull e_isbn from online_identifier
    edition.e_isbn = kbart_data['online_identifier']
    # API data: authors/editors, subject, resource urls, language, description
    ## pull publication date from publicationDate
    edition.published = date.fromisoformat(api_data['publicationDate'])
    # if abstract map to description
    if (not blank_string(api_data['abstract'])): edition.description = api_data['abstract']
    # Contributions
    # creators/creator -> contributor and contribution(role='author')
    ## if more than one creator, first also contribution(role='primary author')
    for index, creator in enumerate(api_data['creators']):
        if (blank_string(creator['creator'])): continue
        contributor = contributor_for_name(creator['creator'])
        role = 'Primary Author' if (index == 0) else 'Author'
        get_one_or_create(db_session, Contribution, contributor_id=contributor.id, edition_id=edition.id, role=role)
    # bookEditors/bookEditor -> contributor and contribution(role='editor')
    for editor in api_data['bookEditors']:
        if (blank_string(editor['bookEditor'])): continue
        contributor = contributor_for_name(editor['bookEditor'])
        get_one_or_create(db_session, Contribution, contributor_id=contributor.id, edition_id=edition.id, role='Editor')

    # Resources
    ## url is typically a list of objects, but can be a single object
    ## if url/format=pdf: add resource(url=url/value)
    resources = api_data['url'] if isinstance(api_data['url'], list) else [api_data['url']] 
    for resource_data in resources:
        if (resource_data['format'] == 'pdf'):
            create_resource = dict(
                edition_id=edition.id, url=resource_data['value'], media_type="application/pdf"
            )
            get_one_or_create(db_session, Resource, **create_resource)

    ## if ePubUrl: add resource(url=ePubUrl)
    if ('ePubUrl' in api_data and not blank_string(api_data['ePubUrl'])):
        create_resource = dict(
            edition_id=edition.id, url=api_data['ePubUrl'], media_type="application/epub+zip"
        )
        get_one_or_create(db_session, Resource, **create_resource)

    # if language is present, map to Palace language
    if (not blank_string(api_data['language'])): edition.language = palace_language(api_data['language']) 
    # if abstract map to description
    if (not blank_string(api_data['abstract'])): edition.description = api_data['abstract']

    return edition

def update_subjects(api_identifier, edition, kbart_data, api_data):
    create_with = dict()
    for subject_value in api_data['subjects']:
        find_with = dict(
            name=subject_value,
        )
        (subject, new) = get_one_or_create(
                db_session, Subject, create_method_kwargs=create_with, **find_with
        )

        find_with = dict(
            edition_id=edition.id,
            subject_id=subject.id
        )
        classification, new = get_one_or_create(
            db_session, Classification, create_method_kwargs=create_with, **find_with
        )
        if api_data['subjects'].index(subject_value) == 0:
            classification.weight = 100
        else:
            classification.weight = 50
    db_session.flush()

def pairtree_for(api_identifier, cache_base_dir):
    md5 = hashlib.md5()
    md5.update(api_identifier.encode('UTF-8'))
    hash_value = md5.hexdigest()
    cache_dir = os.path.join(cache_base_dir, hash_value[0:2], hash_value[2:4])
    os.makedirs(cache_dir, exist_ok=True)
    cache_suffix = api_identifier[len('doi:10.1007/'):len(api_identifier)]
    cache_name = '%s.json' % cache_suffix
    return os.path.join(cache_dir, cache_name)

def read_api_cache(api_identifier):
    cache_base_dir = config['SPRINGER']['apiCache']
    api_cache_path = pairtree_for(api_identifier, cache_base_dir)
    if os.path.isfile(api_cache_path):
        with open(api_cache_path) as crawl_file:
            crawl_json = json.loads(crawl_file.read())
            if crawl_json == None: return dict()
            cache_data = crawl_json['records'][0]
            cache_data['subjects'] = []
            for facet in crawl_json['facets']:
                if facet['name'] == 'subject':
                    cache_data['subjects'] = [value["value"] for value in facet['values']]
            return cache_data
    else:
        return {}

def api_data_for(api_identifier):
    return read_api_cache(api_identifier)

def load_edition(kbart_data):
    edition = None
    new_edition = False
    kbart_identifier = kbart_data['title_id']
    api_identifier = "doi:" + kbart_identifier
    edition = edition_for_identifier(api_identifier)
    if (edition == None):
        edition = stub_edition(api_identifier)[0]
        new_edition = True
    api_data = api_data_for(api_identifier)
    if blank_value(api_data):
        return (None, False)
    update_edition(api_identifier, edition, kbart_data, api_data)
    update_subjects(api_identifier, edition, kbart_data, api_data)

    return (api_identifier, new_edition)

def main():
    create_with = dict()
    num_identifiers = 0
    crawl_log_path = config['SPRINGER']['apiCache']
    kbart_path = config['CSV']['kbart']

    with open(kbart_path, newline='') as kbart_file:
        csv_reader = csv.DictReader(kbart_file, delimiter='\t', quotechar='"')
        identifier = None
        new = False
        for kbart_data in csv_reader:
            (identifier, new) = load_edition(kbart_data)
            if (new):
                num_identifiers += 1
        db_session.flush()
    db_session.commit()
    print("%s new titles" % (str(num_identifiers)))

if __name__ == "__main__":
    main()
