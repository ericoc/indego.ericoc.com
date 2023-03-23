#!/usr/bin/env python3
"""
https://indego.ericoc.com
https://github.com/ericoc/indego.ericoc.com
psql_insert.py
"""
import logging

import requests

from database import db_session
from models import Indego


# Configure logging
logging.basicConfig(
    datefmt='%Y-%m-%d %H:%M:%S %Z', level=logging.INFO,
    format='%(asctime)s [%(levelname)s] (%(process)d): %(message)s',
    handlers=[logging.StreamHandler()]
)

# Set up an HTTPS request to the Indego bike-share JSON API
ua = 'Indego Python3 API Library - https://github.com/ericoc/indego-py-lib'
headers = {'Accept': 'application/json', 'User-Agent': ua}
timeout = 30
url = 'https://kiosks.bicycletransit.workers.dev/phl'
indego = None

try:
    # Make the requests for JSON data
    indego = requests.get(headers=headers, timeout=timeout, url=url)
    indego.raise_for_status()

    # Add PostgreSQL row, using JSON data from Indego API response
    new = Indego(data=indego.json())
    db_session.add(new)
    db_session.commit()
    logging.info('OK')

# Log and exit if something went wrong
except Exception as err:
    logging.exception(err)
    logging.fatal(indego)
