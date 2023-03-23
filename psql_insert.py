#!/usr/bin/env python3
'''
https://indego.ericoc.com
https://github.com/ericoc/indego.ericoc.com
psql_insert.py
'''
import logging
import sys

import requests

from database import db_session
from models import Indego


# Configure logging
logging.basicConfig(
    datefmt='%Y-%m-%d %H:%M:%S %Z', level=logging.INFO,
    format='%(asctime)s [%(levelname)s] (%(process)d): %(message)s',
    handlers=[logging.StreamHandler()]
)

# Make a request to the Indego bike-share API
indego = requests.get(
    headers={'Accept': 'application/json',
             'User-Agent': 'Indego Python3 API Library - https://github.com/ericoc/indego-py-lib'},
    timeout=30, url='https://kiosks.bicycletransit.workers.dev/phl'
)

# Proceed if it was a successful response
if indego.status_code == 200:

    # Create a new PostgreSQL database row,
    #   using the data from the JSON API response
    new = Indego(data=indego.json())
    db_session.add(new)
    db_session.commit()
    logging.info('OK')
    sys.exit(0)

# Log and exit if something went wrong
logging.fatal(indego)
sys.exit(1)
