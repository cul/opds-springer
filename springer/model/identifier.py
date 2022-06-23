from . import Base
from sqlalchemy import Column, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import relationship

# abbreviated from ThePalaceProject/circulation/core/model/identifier.py
class Equivalency(Base):
    """An assertion that two Identifiers identify the same work.
    """

    __tablename__ = "equivalents"

    # 'input' is the ID that was used as input to the datasource.
    # 'output' is the output
    id = Column(Integer, primary_key=True)
    input_id = Column(Integer, ForeignKey("identifiers.id"), index=True)
    input = relationship("Identifier", foreign_keys=input_id)
    output_id = Column(Integer, ForeignKey("identifiers.id"), index=True)
    output = relationship("Identifier", foreign_keys=output_id)

    # Who says?
    data_source_id = Column(Integer, ForeignKey("datasources.id"), index=True)

# abbreviated from ThePalaceProject/circulation/core/model/identifier.py
class Identifier(Base):
    __tablename__ = 'identifiers'
    id = Column(Integer, primary_key=True)
    type = Column(String(64))
    identifier = Column(String(64))
    classifications = relationship("Classification", back_populates="identifier", cascade="all, delete-orphan")
    resources = relationship("Resource", back_populates="identifier", cascade="all, delete-orphan")
    editions = relationship("Edition", back_populates="primary_identifier")
    equivalent_identifiers = relationship("Identifier",
        secondary="equivalents",
        primaryjoin=id==Equivalency.input_id,
        secondaryjoin=id==Equivalency.output_id
    )
    __table_args__ = (UniqueConstraint("type", "identifier"),)
