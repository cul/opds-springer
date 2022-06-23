import warnings

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError, SAWarning
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from sqlalchemy.sql import compiler, select
from sqlalchemy.sql.expression import literal_column, table

from typing import Dict

DEBUG = False

Base = declarative_base()

def flush(db):
    """Flush the database connection unless it's known to already be flushing."""
    is_flushing = False
    if hasattr(db, "_flushing"):
        # This is a regular database session.
        is_flushing = db._flushing
    elif hasattr(db, "registry"):
        # This is a flask_scoped_session scoped session.
        is_flushing = db.registry()._flushing
    else:
        logging.error("Unknown database connection type: %r", db)
    if not is_flushing:
        db.flush()


def create(db, model, create_method="", create_method_kwargs=None, **kwargs):
    kwargs.update(create_method_kwargs or {})
    created = getattr(model, create_method, model)(**kwargs)
    db.add(created)
    flush(db)
    return created, True

def get_one(db, model, on_multiple="error", constraint=None, **kwargs):
    """Gets an object from the database based on its attributes.

    :param constraint: A single clause that can be passed into
        `sqlalchemy.Query.filter` to limit the object that is returned.
    :return: object or None
    """
    constraint = constraint
    if "constraint" in kwargs:
        constraint = kwargs["constraint"]
        del kwargs["constraint"]

    q = db.query(model).filter_by(**kwargs)
    if constraint is not None:
        q = q.filter(constraint)

    try:
        return q.one()
    except MultipleResultsFound:
        if on_multiple == "error":
            raise
        elif on_multiple == "interchangeable":
            # These records are interchangeable so we can use
            # whichever one we want.
            #
            # This may be a sign of a problem somewhere else. A
            # database-level constraint might be useful.
            q = q.limit(1)
            return q.one()
    except NoResultFound:
        return None


def get_one_or_create(db, model, create_method="", create_method_kwargs=None, **kwargs):
    one = get_one(db, model, **kwargs)
    if one:
        return one, False
    else:
        __transaction = db.begin_nested()
        try:
            # These kwargs are supported by get_one() but not by create().
            get_one_keys = ["on_multiple", "constraint"]
            for key in get_one_keys:
                if key in kwargs:
                    del kwargs[key]
            obj = create(db, model, create_method, create_method_kwargs, **kwargs)
            __transaction.commit()
            return obj
        except IntegrityError as e:
            logging.info(
                "INTEGRITY ERROR on %r %r, %r: %r",
                model,
                create_method_kwargs,
                kwargs,
                e,
            )
            __transaction.rollback()
            return db.query(model).filter_by(**kwargs).one(), False

class SessionManager(object):
    engine_for_url: Dict[str, Engine] = {}

    @classmethod
    def engine(cls, url=None):
        url = url or Configuration.database_url()
        return create_engine(url, echo=DEBUG)

    @classmethod
    def initialize(cls, url, initialize_data=True, initialize_schema=True):
        """Initialize the database.

        This includes the schema, the custom functions, and the
        initial content.
        """
        if url in cls.engine_for_url:
            engine = cls.engine_for_url[url]
            return engine, engine.connect()

        engine = cls.engine(url)
        if initialize_schema:
            cls.initialize_schema(engine)
        connection = engine.connect()

        if initialize_data:
            session = Session(connection)
            cls.initialize_data(session)

        if connection:
            connection.close()

        if initialize_schema and initialize_data:
            # Only cache the engine if all initialization has been performed.
            #
            # Some pieces of code (e.g. the script that runs
            # migrations) have a legitimate need to bypass some of the
            # initialization, but normal operation of the site
            # requires that everything be initialized.
            #
            # Until someone tells this method to initialize
            # everything, we can't short-circuit this method with a
            # cache.
            cls.engine_for_url[url] = engine
        return engine, engine.connect()

    @classmethod
    def initialize_schema(cls, engine):
        """Initialize the database schema."""
        # Use SQLAlchemy to create all the tables.
        to_create = [
            table_obj
            for name, table_obj in list(Base.metadata.tables.items())
            if not name.startswith("mv_")
        ]
        Base.metadata.create_all(engine, tables=to_create)

    @classmethod
    def session(cls, url, initialize_data=True, initialize_schema=True):
        engine = connection = 0
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=SAWarning)
            engine, connection = cls.initialize(
                url,
                initialize_data=initialize_data,
                initialize_schema=initialize_schema,
            )
        session = Session(connection)
        if initialize_data:
            session = cls.initialize_data(session)
        return session

    @classmethod
    def initialize_data(cls, session, set_site_configuration=True):
        return session

from .datasource import DataSource
from .identifier import Equivalency, Identifier
from .classification import Classification, Genre, Subject, IdentifierGenre
from .contribution import Contribution, Contributor
from .edition import Edition
from .resource import Resource
