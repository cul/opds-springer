import csv
import os
from sqlalchemy import *
from sqlalchemy.engine.url import make_url
from springer import blank_string, config, db_session
from springer.model import SessionManager, Identifier, Subject, Classification, DataSource, get_one_or_create
from springer.subjects.csv_data import generate_subjects

def main():
    find_with = dict(
        name='SpringerNature',
        primary_identifier_type='DOI'
    )
    create_with = dict()
    data_source, new = get_one_or_create(
        db_session, DataSource, create_method_kwargs=create_with, **find_with
    )
    num_identifiers = 0
    num_subjects = 0
    csv_path = config['CSV']['springerSubjects']
    with open(csv_path, newline='') as csvfile:
        csv_reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        identifier = None
        new = False
        for csv_subject in generate_subjects(csv_reader):
            if (blank_string(csv_subject['doi'])): continue
            find_with = dict(
                identifier=csv_subject['doi'],
                type='DOI'
            )
            if (identifier == None) or (identifier.identifier != csv_subject['doi']):
                if (identifier != None): db_session.commit()
                (identifier, new) = get_one_or_create(
                    db_session, Identifier, create_method_kwargs=create_with, **find_with
                )
                if (new):
                    num_identifiers += 1
            find_with = dict(
                name=csv_subject['name'],
            )
            (subject, new) = get_one_or_create(
                db_session, Subject, create_method_kwargs=create_with, **find_with
            )
            if (new): num_subjects += 1

            find_with = dict(
                identifier_id=identifier.id,
                subject_id=subject.id,
                data_source_id=data_source.id
            )
            classification, new = get_one_or_create(
                db_session, Classification, create_method_kwargs=create_with, **find_with
            )
            if csv_subject['primary']:
                classification.weight = 100
            else:
                classification.weight = 50
        db_session.commit()
    print("%s new subjects, %s new identifiers" % (str(num_subjects), str(num_identifiers)))

if __name__ == "__main__":
    main()
