from . import Base
from sqlalchemy import Column, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import relationship

class Resource(Base):
    """This model denormalizes three entities in ThePalaceProject/circulation
    It combines resources, hyperlinks, and representations for the narrow needs of the opds feed.
    """

    __tablename__ = "resources"

    id = Column(Integer, primary_key=True)

    # A URI that uniquely identifies this resource. Most of the time
    # this will be an HTTP URL, which is why we're calling it 'url',
    # but it may also be a made-up URI.
    url = Column(String(1024), index=True)

    ## This column taken from the Hyperlink class in ThePalaceProject/circulation
    ## which is a join table between identifiers and resources
    # A Hyperlink is always associated with some Identifier.
    edition_id = Column(
        Integer, ForeignKey("editions.id"), index=True, nullable=False
    )
    edition = relationship("Edition", foreign_keys=edition_id)

    ## This column taken from the Hyperlink class in ThePalaceProject/circulation
    ## which is a join table between identifiers and resources
    ## in the Springer data we are only concerned with "http://opds-spec.org/acquisition"
    # The link relation between the Identifier and the Resource.
    rel = Column(String(32), index=False, nullable=False, default="http://opds-spec.org/acquisition")

    ## This column taken from the Representation class in ThePalaceProject/circulation
    ## which is a reusable representation of a downloaded file associated with Resource
    ## in the Springer data we are only concerned with "application/epub+zip" and "application/pdf"
    # The media type of the representation.
    media_type = Column(String(32), index=True, nullable=False)

    # URL must be unique.
    __table_args__ = (UniqueConstraint("url"),)

