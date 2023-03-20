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


logging.basicConfig(
    datefmt='%Y-%m-%d %H:%M:%S %Z', level=logging.INFO,
    format='%(asctime)s [%(levelname)s] (%(process)d): %(message)s',
    handlers=[logging.StreamHandler()]
)

indego = requests.get(
    headers={'Accept': 'application/json',
             'User-Agent': 'Indego Python3 API Library - https://github.com/ericoc/indego-py-lib'},
    timeout=30, url='https://kiosks.bicycletransit.workers.dev/phl'
)

if indego.status_code == 200:
    new = Indego(data=indego.json())
    db_session.add(new)
    db_session.commit()
    logging.info('OK')
    sys.exit(0)

logging.fatal(indego)
sys.exit(1)
