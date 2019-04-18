indego.ericoc.com
==============================

About
-----

I previously created [a similar website in PHP](https://github.com/ericoc/indegophp.ericoc.com) and I have tried to replicate it here using Python.

I previously made [this Python library](https://github.com/ericoc/indego-py-lib) for the Philadelphia Indego bike-share program to familiarize myself with Python for the first time.

I decided to use the Python library that I wrote to generate pretty current and historical graphs of bicycle availability at https://indego.ericoc.com/ as a way to get even more familiar with Python. 

The website uses Flask and I tried to keep it pretty simple since I am (clearly) not a stylish web designer, by any means. I love using simple block characters (█) of different colors to represent bicycles or empty docks at each bike-share station.

Historical Data
---------------

In any case, I have been running [this PHP script](https://github.com/ericoc/indegophp.ericoc.com/blob/master/backend/db_insert.php) on my personal server every 10 minutes for a few years. It has been collecting data from the Philadelphia Indego bike-share API and storing it in a MySQL database. I can tell you how many bikes and empty docks were at each bike-share station in Philadelphia (at 10-minute intervals, anyways) since some time in November of 2015.

As of August 2018, I have a total of approximately 15.2 million rows or ~900MB of MySQL data (`.ibd` file size). For the station closest to my apartment, I have approximately 140,000 records.

Charts
------

With the data that I have recorded from the Indego API, I use [Highcharts](http://www.highcharts.com/) to generate historical graphs of each station. I even got to write [this blog post](https://www.highcharts.com/blog/products/highcharts/250-tracking-bike-share-usage-in-philadelphia/) (for the Highcharts blog)!

I was inspired by the awesome graphs showing the availability of bikes at each station during commuting times on [Randal Olsons blog here](http://www.randalolson.com/2015/09/05/visualizing-indego-bike-share-usage-patterns-in-philadelphia-part-2/)!

More Information
----------------
* [Highcharts Blog](http://www.highcharts.com/blog)
* [Official Philadelphia Indego Bike Share website](https://www.rideindego.com/)
* [The actual Indego API](https://www.rideindego.com/stations/json/) (a GeoJSON file)
* [OpenDataPhilly description of the Indego API](https://www.opendataphilly.org/dataset/bike-share-stations)
