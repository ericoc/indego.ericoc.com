#!/usr/bin/env python3

from indego import Indego
import pymysql
import db_creds_rw

# Wrap this whole thing in a big try to catch any and all exceptions
try:

    # Connect to MySQL (with read-write credentials)
    dbh = pymysql.connect(host=db_creds_rw.db_creds_rw['host'], user=db_creds_rw.db_creds_rw['user'], passwd=db_creds_rw.db_creds_rw['passwd'], db=db_creds_rw.db_creds_rw['db'])

    # Get all Indego stations from the API
    indego = Indego()
    indego_stations = indego.get_stations()

    # Open a MySQL database cursor
    with dbh.cursor() as dbc:

        # Loop through each bicycle-share station
        for indego_station in indego_stations.values():

            # Print out which station is being processed
            print("%s / %s" % (indego_station['kioskId'], indego_station['name']))

            # Create named parameters to use within the MySQL query to insert/update station information
            station_values = {
                'kioskId' : indego_station['kioskId'],
                'name' : indego_station['name'],
                'addressStreet' : indego_station['addressStreet'],
                'addressCity' : indego_station['addressCity'],
                'addressState' : indego_station['addressState'],
                'addressZipCode' : indego_station['addressZipCode']
            }

            # Create the query to insert (or update) basic station information
            print("Station: ", end='')
            insert_station = ("INSERT INTO `stations` (`kioskId`, `name`, `addressStreet`, `addressCity`, `addressState`, `addressZipCode`, `added`)"
                              "VALUES (%(kioskId)s, %(name)s, %(addressStreet)s, %(addressCity)s, %(addressState)s, %(addressZipCode)s, NOW())"
                              "ON DUPLICATE KEY UPDATE `name` = %(name)s, `addressStreet` = %(addressStreet)s, `addressCity` = %(addressCity)s, `addressState` = %(addressState)s, `addressZipCode` = %(addressZipCode)s")

            # Fill in the station details and execute the query
            dbc.execute(insert_station, station_values)
            print('OK')

            # Create named parameters to use within the MySQL query to insert availability data for the station
            data_values = {
                'kioskId' : indego_station['kioskId'],
                'kioskPublicStatus' : indego_station['kioskPublicStatus'],
                'bikesAvailable' : indego_station['bikesAvailable'],
                'docksAvailable' : indego_station['docksAvailable'],
                'totalDocks' : indego_station['totalDocks']
            }

            # Create the query to insert availability data for the station
            print("Data: ", end='')
            insert_data = ("INSERT INTO `data` (`kioskId`, `kioskPublicStatus`, `bikesAvailable`, `docksAvailable`, `totalDocks`, `added`)"
                           "VALUES (%(kioskId)s, %(kioskPublicStatus)s, %(bikesAvailable)s, %(docksAvailable)s, %(totalDocks)s, NOW())")

            # Fill in the bicycle availability data values and execute the query
            dbc.execute(insert_data, data_values)
            print('OK')

    # End database cursor, commit the transaction, and close the MySQL connection
    dbh.commit()
    dbh.close()

# Print any exceptions
except Exception as e:
    print(e)
