# encoding: utf-8
# DataSource

from . import Base
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

class DataSourceConstants(object):
    GUTENBERG = "Gutenberg"
    OVERDRIVE = "Overdrive"
    ODILO = "Odilo"
    PROJECT_GITENBERG = "Project GITenberg"
    STANDARD_EBOOKS = "Standard Ebooks"
    UNGLUE_IT = "unglue.it"
    BIBLIOTHECA = "Bibliotheca"
    OCLC = "OCLC Classify"
    OCLC_LINKED_DATA = "OCLC Linked Data"
    AMAZON = "Amazon"
    XID = "WorldCat xID"
    AXIS_360 = "Axis 360"
    WEB = "Web"
    OPEN_LIBRARY = "Open Library"
    CONTENT_CAFE = "Content Cafe"
    VIAF = "VIAF"
    GUTENBERG_COVER_GENERATOR = "Gutenberg Illustrated"
    GUTENBERG_EPUB_GENERATOR = "Project Gutenberg EPUB Generator"
    METADATA_WRANGLER = "Library Simplified metadata wrangler"
    MANUAL = "Manual intervention"
    NOVELIST = "NoveList Select"
    NYT = "New York Times"
    NYPL_SHADOWCAT = "NYPL Shadowcat"
    LIBRARY_STAFF = "Library staff"
    ADOBE = "Adobe DRM"
    PLYMPTON = "Plympton"
    ELIB = "eLiburutegia"
    OA_CONTENT_SERVER = "Library Simplified Open Access Content Server"
    PRESENTATION_EDITION = "Presentation edition generator"
    INTERNAL_PROCESSING = "Library Simplified Internal Process"
    FEEDBOOKS = "FeedBooks"
    BIBBLIO = "Bibblio"
    ENKI = "Enki"
    LCP = "LCP"
    PROQUEST = "ProQuest"
    SPRINGER = "Springer"

    DEPRECATED_NAMES = {"3M": BIBLIOTHECA}
    THREEM = BIBLIOTHECA

    # Some sources of open-access ebooks are better than others. This
    # list shows which sources we prefer, in ascending order of
    # priority. unglue.it is lowest priority because it tends to
    # aggregate books from other sources. We prefer books from their
    # original sources.
    OPEN_ACCESS_SOURCE_PRIORITY = [
        UNGLUE_IT,
        GUTENBERG,
        GUTENBERG_EPUB_GENERATOR,
        PROJECT_GITENBERG,
        ELIB,
        FEEDBOOKS,
        PLYMPTON,
        STANDARD_EBOOKS,
    ]

# abbreviated from ThePalaceProject/circulation/core/model/datasource.py
class DataSource(Base, DataSourceConstants):

    """A source for information about books, and possibly the books themselves."""

    __tablename__ = "datasources"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, index=True)
    offers_licenses = Column(Boolean, default=False)
    primary_identifier_type = Column(String, index=True)

    # One DataSource can generate many Editions.
    editions = relationship("Edition", backref="data_source")

    # One DataSource can generate many IDEquivalencies.
    id_equivalencies = relationship("Equivalency", backref="data_source")

    # One DataSource can provide many Classifications.
    classifications = relationship("Classification", backref="data_source")
