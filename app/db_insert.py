#!/usr/bin/env python3

from indego import Indego
import pymysql
import db_creds_rw

try:

    dbh = pymysql.connect(host=db_creds_rw.db_creds_rw['host'], user=db_creds_rw.db_creds_rw['user'], passwd=db_creds_rw.db_creds_rw['passwd'], db=db_creds_rw.db_creds_rw['db'])

    indego = Indego()
    indego_stations = indego.get_stations()

    with dbh.cursor() as dbc:

        for indego_station in indego_stations.values():

            print("%s / %s" % (indego_station['kioskId'], indego_station['name']))

            station_values = {
                'kioskId' : indego_station['kioskId'],
                'name' : indego_station['name'],
                'addressStreet' : indego_station['addressStreet'],
                'addressCity' : indego_station['addressCity'],
                'addressState' : indego_station['addressState'],
                'addressZipCode' : indego_station['addressZipCode']
            }

            print("Station: ", end='')
            insert_station = ("INSERT INTO `stations` (`kioskId`, `name`, `addressStreet`, `addressCity`, `addressState`, `addressZipCode`, `added`)"
                              "VALUES (%(kioskId)s, %(name)s, %(addressStreet)s, %(addressCity)s, %(addressState)s, %(addressZipCode)s, NOW())"
                              "ON DUPLICATE KEY UPDATE `name` = %(name)s, `addressStreet` = %(addressStreet)s, `addressCity` = %(addressCity)s, `addressState` = %(addressState)s, `addressZipCode` = %(addressZipCode)s")

            dbc.execute(insert_station, station_values)
            print('OK')


            data_values = {
                'kioskId' : indego_station['kioskId'],
                'kioskPublicStatus' : indego_station['kioskPublicStatus'],
                'bikesAvailable' : indego_station['bikesAvailable'],
                'docksAvailable' : indego_station['docksAvailable'],
                'totalDocks' : indego_station['totalDocks']
            }

            print("Data: ", end='')
            insert_data = ("INSERT INTO `data` (`kioskId`, `kioskPublicStatus`, `bikesAvailable`, `docksAvailable`, `totalDocks`, `added`)"
                           "VALUES (%(kioskId)s, %(kioskPublicStatus)s, %(bikesAvailable)s, %(docksAvailable)s, %(totalDocks)s, NOW())")

            dbc.execute(insert_data, data_values)
            print('OK')

    dbh.commit()

    dbh.close()

except Exception as e:
    print(e)
