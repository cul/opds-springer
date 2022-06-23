# encoding: utf-8
# Subject, Classification

from . import Base, Identifier
from sqlalchemy import Column, ForeignKey, Integer, String, Table, UniqueConstraint
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import relationship

# abbreviated from ThePalaceProject/circulation/core/model/classification.py
class Subject(Base):
    __tablename__ = 'subjects'
    __table_args__ = (UniqueConstraint("type","name"),)
    id = Column(Integer, primary_key=True)
    type = Column(String(32))
    name = Column(String(256))
    classifications = relationship("Classification", back_populates="subject", cascade="all, delete-orphan")

class Classification(Base):
    __tablename__ = 'classifications'
    __table_args__ = (UniqueConstraint("identifier_id","subject_id","data_source_id"),)
    id = Column(Integer, primary_key=True)
    identifier_id = Column(Integer, ForeignKey("identifiers.id"), index=True)
    identifier = relationship("Identifier", foreign_keys=identifier_id)

    subject_id = Column(Integer, ForeignKey("subjects.id"), index=True)
    subject = relationship("Subject", foreign_keys=subject_id)
    data_source_id = Column(Integer, ForeignKey("datasources.id"), index=True)

    weight = Column(Integer)

class IdentifierGenre(Base):
    __tablename__ = "identifier_genres"
    identifier_id = Column(Integer, ForeignKey("identifiers.id"), primary_key=True)
    genre_id = Column(Integer, ForeignKey("genres.id"), primary_key=True)


class Genre(Base):
    __tablename__ = "genres"
    id = Column(Integer, primary_key=True)
    name = Column(String(256), unique=True, index=True)

    # One Genre may participate in many WorkGenre assignments.
    identifiers = association_proxy("identifier_genres", "identifier")

    identifier_genres = relationship(
        "IdentifierGenre", backref="genre", cascade="all, delete-orphan"
    )

    @classmethod
    def lookup(cls, _db, name, autocreate=False, use_cache=True):
        def create():
            """Function called when a Genre is not found in cache and must be
            created."""
            new = False
            args = (_db, Genre)
            if autocreate:
                genre, new = get_one_or_create(*args, name=name)
            else:
                genre = get_one(*args, name=name)
                if genre is None:
                    logging.getLogger().error('"%s" is not a recognized genre.', name)
                    return None, False
            return genre, new

        return create()
