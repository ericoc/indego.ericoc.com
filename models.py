"""
https://indego.ericoc.com
https://github.com/ericoc/indego.ericoc.com
models.py
"""
from sqlalchemy import Column, DateTime, text, Text
from sqlalchemy.dialects.postgresql import JSONB

from database import Base, metadata

class Indego(Base):
    """
    Indego bike-share API station data database model.
    """
    __tablename__ = 'indego'

    # Timestamp when the row was added
    added = Column(DateTime(True),
                   primary_key=True,
                   server_default=text('NOW()'))

    # JSONB response data from the Indego HTTPS API at the time
    data = Column(JSONB(astext_type=Text()))

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f'Indego: {len(self.data)} @ {self.added}'
