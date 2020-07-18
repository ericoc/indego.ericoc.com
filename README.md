[indego.ericoc.com](https://indego.ericoc.com/)
=================

About
-----

I previously created [a similar website in PHP](https://github.com/ericoc/indegophp.ericoc.com) and I have tried to replicate it here using Python.

I previously made [this Python library](https://github.com/ericoc/indego-py-lib) for the Philadelphia Indego bike-share program to familiarize myself with Python for the first time.

I decided to use the Python library that I wrote to generate pretty current and historical graphs of bicycle availability at https://indego.ericoc.com/ as a way to get even more familiar with Python. 

The website uses Flask and I tried to keep it pretty simple since I am (clearly) not a stylish web designer, by any means. I love using simple block characters (█) of different colors to represent bicycles or empty docks at each bike-share station.

Data
---------------

I previously stored historical data from the Philadelphia Indego bike-share API in a MySQL database.
However, I am currently storing the complete JSON response in PostgreSQL every ten (10) minutes:

    indego=> select now();
                  now
    -------------------------------
     2020-07-18 21:19:36.550102+00
    (1 row)

    indego=> select min(added) from indego;
                  min
    -------------------------------
     2019-05-01 01:00:41.994451+00
    (1 row)

    indego=> select count(added) from indego;
     count
    -------
     63919
    (1 row)

This PostgreSQL database powers the historical charts on the website.

Charts
------
With the data that I have recorded from the Indego API, I use [Highcharts](http://www.highcharts.com/) to generate historical graphs of each station.
I even got to write [this blog post](https://www.highcharts.com/blog/products/highcharts/250-tracking-bike-share-usage-in-philadelphia/) (for the Highcharts blog)!

I was inspired by the awesome graphs showing the availability of bikes at each station during commuting times on [Randal Olsons blog here](http://www.randalolson.com/2015/09/05/visualizing-indego-bike-share-usage-patterns-in-philadelphia-part-2/)!

More Information
----------------
* [Highcharts Blog](http://www.highcharts.com/blog)
* [Official Philadelphia Indego Bike Share website](https://www.rideindego.com/)
* [The actual Indego API](https://www.rideindego.com/stations/json/) (a GeoJSON file)
* [OpenDataPhilly description of the Indego API](https://www.opendataphilly.org/dataset/bike-share-stations)
