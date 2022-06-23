import os
import json
from datetime import date
from springer import blank_string, config, db_session
from springer.mappings import palace_language
from springer.model import (
    SessionManager, Identifier, Genre, IdentifierGenre, Classification, Contribution, Contributor,
    DataSource, Edition, Equivalency, Resource, create, get_one_or_create
)
from sqlalchemy import *
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm.exc import NoResultFound

def edition_for_identifier(identifier):
    q = db_session.query(Edition).filter_by(primary_identifier_id=identifier.id)

    try:
        return q.one()
    except NoResultFound:
        return None

def stub_edition(data_source, identifier):
    return create(db_session, Edition, data_source_id=data_source.id, primary_identifier_id=identifier.id)

def contributor_for_name(name):
    find_with=dict(name=name)
    create_with = dict()
    (contributor, new) = get_one_or_create(
        db_session, Contributor, create_method_kwargs=create_with, **find_with
    )
    return contributor

def equate_identifier_to(data_source, primary_identifier, **find_with):
    (equivalent, new) = get_one_or_create(
        db_session, Identifier, **find_with
    )
    (equivalency, new) = get_one_or_create(
        db_session, Equivalency, input_id=primary_identifier.id, output_id=equivalent.id, data_source_id=data_source.id
    )
    return equivalency

def update_edition(data_source, identifier, edition, edition_data):
    # Contributions
    # creators/creator -> contributor and contribution(role='author')
    ## if more than one creator, first also contribution(role='primary author')
    for index, creator in enumerate(edition_data['creators']):
        if (blank_string(creator['creator'])): continue
        contributor = contributor_for_name(creator['creator'])
        role = 'Primary Author' if (index == 0) else 'Author'
        get_one_or_create(db_session, Contribution, contributor_id=contributor.id, edition_id=edition.id, role=role)
    # bookEditors/bookEditor -> contributor and contribution(role='editor')
    for editor in edition_data['bookEditors']:
        if (blank_string(editor['bookEditor'])): continue
        contributor = contributor_for_name(editor['bookEditor'])
        get_one_or_create(db_session, Contribution, contributor_id=contributor.id, edition_id=edition.id, role='Editor')

    # Identifier Equivalencies
    ## map isbn to identifer(type='ISBN'), and equivalent to doi
    if (not blank_string(edition_data['isbn'])):
        equate_identifier_to(data_source, identifier, type='ISBN', identifier=edition_data['isbn'])
    if (not blank_string(edition_data['printIsbn'])):
        if (edition_data['isbn'] != edition_data['printIsbn']):
            equate_identifier_to(data_source, identifier, type='ISBN', identifier=edition_data['printIsbn'])
    ## TODO/Lyrasis: EISBN is not a defined type in IdentifierConstants
    if (not blank_string(edition_data['electronicIsbn'])):
        if (edition_data['isbn'] != edition_data['electronicIsbn']):
            equate_identifier_to(data_source, identifier, type='ISBN', identifier=edition_data['electronicIsbn'])

    # Resources
    ## url is typically a list of objects, but can be a single object
    ## if url/format=pdf: add resource(url=url/value)
    resources = edition_data['url'] if isinstance(edition_data['url'], list) else [edition_data['url']] 
    for resource_data in resources:
        if (resource_data['format'] == 'pdf'):
            create_resource = dict(
                data_source_id=data_source.id, identifier_id=identifier.id, url=resource_data['value'], media_type="application/pdf"
            )
            get_one_or_create(db_session, Resource, **create_resource)

    ## if ePubUrl: add resource(url=ePubUrl)
    if ('ePubUrl' in edition_data and not blank_string(edition_data['ePubUrl'])):
        create_resource = dict(
            data_source_id=data_source.id, identifier_id=identifier.id, url=edition_data['ePubUrl'], media_type="application/epub+zip"
        )
        get_one_or_create(db_session, Resource, **create_resource)

    # if language is present, map to Palace language
    if (not blank_string(edition_data['language'])): edition.language = palace_language(edition_data['language']) 
    # if title is not blank prefer it over publicationName
    if (('publicationName' in edition_data) and (not blank_string(edition_data['publicationName']))):
        edition.title = edition_data['publicationName']
    if (('title' in edition_data) and (not blank_string(edition_data['title']))):
        edition.title = edition_data['title']
    # publisher maps to publisher
    edition.publisher = edition_data['publisher']
    # publicationDate maps to published
    edition.published = date.fromisoformat(edition_data['publicationDate'])
    # if abstract map to description
    if (not blank_string(edition_data['abstract'])): edition.description = edition_data['abstract']
    # TODO/TBD: Genres are in Palace but not OPDS
    ## map resourceType to genres
    ## map genre to genres
    ## build Genre and IdentifierGenres
    # TODO/TBD: if openaccess: ??? use different acquisition strategy?
    # TODO/TBD: if copyright: ???
    return edition

def load_edition(data_source, edition_data):
    find_with = dict(
        identifier=edition_data['doi'],
        type='DOI'
    )
    create_with = dict()
    (identifier, new) = get_one_or_create(
        db_session, Identifier, create_method_kwargs=create_with, **find_with
    )
    edition = None
    if (new):
        edition = stub_edition(data_source, identifier)[0]
    else:
        edition = edition_for_identifier(identifier)
        if (edition == None): edition = stub_edition(data_source, identifier)[0]
    update_edition(data_source, identifier, edition, edition_data)

    return (identifier, new)

def main():
    find_with = dict(
        name='SpringerNature',
        primary_identifier_type='DOI'
    )
    create_with = dict()
    data_source, new = get_one_or_create(
        db_session, DataSource, create_method_kwargs=create_with, **find_with
    )
    db_session.flush()
    num_identifiers = 0
    crawl_log_path = config['SPRINGER']['crawlLog']
    with open(crawl_log_path) as crawl_log:
        for crawl_cache in crawl_log:
            with open(crawl_cache.rstrip()) as crawl_file:
                crawl_json = json.loads(crawl_file.read())
                if crawl_json == None: continue
                for edition_data in crawl_json["records"]:
                    (identifier, new) = load_edition(data_source, edition_data)
                    if (new):
                        num_identifiers += 1
                    db_session.flush()
                db_session.commit()
    print("%s new identifiers" % (str(num_identifiers)))

if __name__ == "__main__":
    main()
