# encoding: utf-8
# Subject, Classification

from . import Base
from sqlalchemy import Column, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

# abbreviated from ThePalaceProject/circulation/core/model/contributor.py
# renamed, like classification, after relation to edition model
class Contributor(Base):
    """Someone (usually human) who contributes to books."""

    __tablename__ = "contributors"
    id = Column(Integer, primary_key=True)

    name = Column(String(128), index=True)

    contributions = relationship("Contribution", backref="contributor")

class Contribution(Base):
    """A contribution made by a Contributor to a Edition."""

    __tablename__ = "contributions"
    id = Column(Integer, primary_key=True)
    edition_id = Column(Integer, ForeignKey("editions.id"), index=True, nullable=False)
    contributor_id = Column(
        Integer, ForeignKey("contributors.id"), index=True, nullable=False
    )
    role = Column(String(32), index=True, nullable=False)
    __table_args__ = (UniqueConstraint("edition_id", "contributor_id", "role"),)


