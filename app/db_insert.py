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

            print("Station: ", end='')
            insert_station = ("INSERT INTO `stations` (`kioskId`, `name`, `addressStreet`, `addressCity`, `addressState`, `addressZipCode`, `added`)"
                              "VALUES (%s, %s, %s, %s, %s, %s, NOW())"
                              "ON DUPLICATE KEY UPDATE `name` = %s, `addressStreet` = %s, `addressCity` = %s, `addressState` = %s, `addressZipCode` = %s")

            station_values = (indego_station['kioskId'], indego_station['name'], indego_station['addressStreet'], indego_station['addressCity'], indego_station['addressState'], indego_station['addressZipCode'], indego_station['name'], indego_station['addressStreet'], indego_station['addressCity'], indego_station['addressState'], indego_station['addressZipCode'])
            dbc.execute(insert_station, station_values)
            print('OK')

            print("Data: ", end='')
            insert_data = ("INSERT INTO `data` (`kioskId`, `kioskPublicStatus`, `bikesAvailable`, `docksAvailable`, `totalDocks`, `added`)"
                           "VALUES (%s, %s, %s, %s, %s, NOW())")

            data_values = (indego_station['kioskId'], indego_station['kioskPublicStatus'], indego_station['bikesAvailable'], indego_station['docksAvailable'], indego_station['totalDocks'])
            dbc.execute(insert_data, data_values)
            print('OK')

    dbh.commit()

    dbh.close()

except Exception as e:
    print(e)
