"""
https://indego.ericoc.com
https://github.com/ericoc/indego.ericoc.com
database.py
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

from config import SQLALCHEMY_DATABASE_URI, SQLALCHEMY_ECHO

engine = create_engine(
    url=SQLALCHEMY_DATABASE_URI,
    echo=SQLALCHEMY_ECHO,
    pool_pre_ping=True
)

db_session = scoped_session(
    sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )
)

Base = declarative_base()
Base.query = db_session.query_property()
metadata = Base.metadata
