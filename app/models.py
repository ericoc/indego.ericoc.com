from app import app
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, DateTime, JSON, MetaData, func
from sqlalchemy.schema import FetchedValue

# Connect to the database
db = SQLAlchemy(app)

"""
Create a class for the Indego database
"""
class Indego(db.Model):
    __tablename__   = 'indego'
    added           = Column(DateTime(True), primary_key=True, server_default=FetchedValue())
    data            = Column(JSON)

    def __repr__(self):
        return f'<Indego> "{added}" : "{data}"'
