# encoding: utf-8
# Subject, Classification

from . import Base
from sqlalchemy import Column, Date, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

# abbreviated from ThePalaceProject/circulation
class EditionConstants(object):
    BOOK_MEDIUM = "Book"

    # These are all media known to the system.
    KNOWN_MEDIA = (
        BOOK_MEDIUM,
    )

    FULFILLABLE_MEDIA = [BOOK_MEDIUM]

    medium_to_additional_type = {
        BOOK_MEDIUM: "http://schema.org/EBook",
    }

    additional_type_to_medium = {}
    for k, v in list(medium_to_additional_type.items()):
        additional_type_to_medium[v] = k

    additional_type_to_medium["http://schema.org/Book"] = BOOK_MEDIUM

    # Map the medium constants to the strings used when generating
    # permanent work IDs.
    medium_for_permanent_work_id = {
        BOOK_MEDIUM: "book",
    }

# abbreviated from ThePalaceProject/circulation/core/model/edition.py
class Edition(Base, EditionConstants):
    __tablename__ = "editions"
    id = Column(Integer, primary_key=True)

    primary_identifier = Column(String(64))
    print_isbn = Column(String(64))
    e_isbn = Column(String(64))
    bib_id = Column(String(64))

    title = Column(String(512), index=True)

    classifications = relationship("Classification")
    contributions = relationship("Contribution", backref="edition")
    resources = relationship("Resource")

    language = Column(String(16), index=True)
    publisher = Column(String(128), index=True)

    published = Column(Date)

    MEDIUM_ENUM = Enum(*EditionConstants.KNOWN_MEDIA, name="medium")

    medium = Column(MEDIUM_ENUM, index=True, default='Book')

    description = Column(String(4096))

    cover_full_url = Column(String(1024))
    cover_thumbnail_url = Column(String(1024))
