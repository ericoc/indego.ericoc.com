#!/usr/bin/env python3

import requests
import db_creds_rw
import psycopg2

# Wrap this whole thing in a big try to catch any and all exceptions
try:

    # Connect to PostgreSQL (with read-write credentials)
    dbh = psycopg2.connect(
                            user='indego',
                            password=db_creds_rw.db_creds_rw['passwd'],
                            host='localhost',
                            port='5432',
                            database='indego'
                          )

    # Get all Indego stations from the API (but as raw JSON, so not using the library I made...)
    url = 'https://www.rideindego.com/stations/json/'
    user_agent = 'Indego Python3 API Library - https://github.com/ericoc/indego-py-lib'
    headers = {'Accept': 'application/json', 'User-Agent': user_agent}
    indego_data = requests.get(url, headers=headers)

    if indego_data.status_code == 200:
        insert_data = indego_data.text
    else:
        insert_data = None

    # Open a PostgreSQL database cursor, build the query, execute, and commit the transaction
    dbc = dbh.cursor()
    add_data_query = "INSERT INTO indego (added, data) VALUES (NOW(), %s)"
    dbc.execute(add_data_query, (insert_data,))
    dbh.commit()
    count = dbc.rowcount

    # Show number of records successfully inserted (should always be 1)
    print(count, 'record inserted successfully')

    # End database cursor and close the PostgreSQL connection
    dbc.close()
    dbh.close()

# Print any exceptions
except (Exception, psycopg2.Error) as e:
    print(e)
