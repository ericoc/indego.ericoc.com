"""
https://indego.ericoc.com
https://github.com/ericoc/indego.ericoc.com
models.py
"""
from sqlalchemy import Column, DateTime, text, Text
from sqlalchemy.dialects.postgresql import JSONB

from database import Base, metadata


class Indego(Base):
    '''Indego bike-share API data database model'''
    __tablename__ = 'indego'

    added = Column(DateTime(True), primary_key=True,
                   server_default=text('NOW()'))
    data = Column(JSONB(astext_type=Text()))

    def __repr__(self):
        '''repr'''
        return f'<IndegoData> {repr(self.added)} ' \
            f'("{self.added.strftime("%Y-%m-%d %H:%M:%S.%f%z")}"): ' \
            f'{len(self.data)}'
