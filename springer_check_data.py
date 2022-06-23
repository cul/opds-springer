from sqlalchemy.orm import joinedload
from springer import db_session
from springer.model import SessionManager, Identifier, Edition, Subject, Classification, Contribution, DataSource, get_one_or_create

def main():
    q = db_session.query(Identifier).join(Edition, Edition.primary_identifier_id == Identifier.id, isouter=True)
    count = q.filter(Identifier.type == 'DOI').filter(Edition.id == None).count()
    print("%s identifiers have no matching editions" % (count))
    q = db_session.query(Identifier).join(Classification, Classification.identifier_id == Identifier.id, isouter=True)
    no_subjects = q.filter(Identifier.type == 'DOI').filter(Classification.id == None)
    count = no_subjects.count()
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
if __name__ == "__main__":
    main()
