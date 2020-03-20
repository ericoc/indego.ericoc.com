#!/usr/bin/env python3

from indego import Indego
from influxdb import InfluxDBClient

try:

    # Prepare for insertion data, get all Indego stations, and loop through each station
    data = []
    indego = Indego()
    stations = indego.get_stations()
    for station in stations.values():

        # Grab the current station data (just bikesAvailable and docksAvailable measurements for now)
        kioskId = station['kioskId']
        for measurement in ['bikesAvailable', 'docksAvailable']:
            value = station[measurement]
            data.append(f"{measurement},kioskId={kioskId} value={value}")

    # Connect to InfluxDB, insert all station data, and disconnect
    influx = InfluxDBClient(host='127.0.0.1', port=8086, database='indego')
    influx.write_points(data, database='indego', protocol='line')
    influx.close()

# Print any exceptions
except Exception as e:
    print(e)
