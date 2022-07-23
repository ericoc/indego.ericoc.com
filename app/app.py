import re
import psycopg2
import db_creds_ro
from psycopg2.extensions import AsIs
from flask import Flask, make_response, redirect, render_template, request, send_from_directory, url_for

"""
Initialize Flask app
"""
app = Flask(__name__)
app.config.from_pyfile('config.py')

if __name__ == '__main__':
    app.run(debug=True)

# Get database classes
#import models

"""
Define a function to connect to the PostgreSQL database (using read-only credentials)
"""
def dbc():
    try:
        import db_creds_ro
        return psycopg2.connect(
                                user        = db_creds_ro.db_creds['username'],
                                password    = db_creds_ro.db_creds['password'],
                                host        = '127.0.0.1',
                                port        = 5432,
                                database    = 'indego'
                )

    # Print (and return) any exception
    except Exception as e:
        print(f"\n\ndbc:\n{e}\n\n")
        return e


"""
Define a function to find stations, in the latest database entry, based on whatever search string
"""
def find_stations(search=None):

    try:
        # Create a query to find the latest database entry that is not null
        latest_added_query  = """SELECT MAX(added) FROM indego WHERE data IS NOT NULL;"""

        # Connect to the database
        conn = dbc()
        with conn.cursor() as cur:

            # Get the latest added data time
            cur.execute(latest_added_query)
            latest_added    = cur.fetchone()
            added           = latest_added[0]

            default_query   = """SELECT station->'properties'->'id' "kioskId", station->'properties' "properties"   \
                                FROM indego, jsonb_array_elements(indego.data->'features') station  \
                                WHERE added = %s \
                                ORDER BY indego.added DESC;"""

            if not search or search == '':
                cur.execute(default_query, (added,))

            elif isinstance(search, int) or search.isnumeric():

                if len(str(search)) == 5:

                    query   = """SELECT station->'properties'->'id' "kioskId", \
                                    station->'properties' "properties" \
                                 FROM indego, jsonb_array_elements(indego.data->'features') station \
                                 WHERE station->'properties'->>'addressZipCode' = %(search)s \
                                 AND added = %(added)s \
                                 ORDER BY indego.added DESC;"""
                    cur.execute(query, {"search": str(search), "added": added})

                elif len(str(search)) == 4:

                    query   = """SELECT station->'properties'->'id' "kioskId", \
                                    station->'properties' "properties" \
                                 FROM indego, jsonb_array_elements(indego.data->'features') station \
                                 WHERE station->'properties'->>'kioskId' = %(search)s \
                                 AND added = %(added)s \
                                 ORDER BY indego.added DESC;"""
                    cur.execute(query, {"search": str(search), "added": added})

                else:

                    search  = re.sub(r'[^a-zA-Z0-9\&\,\. ]', '', search)
                    query   = """SELECT station->'properties'->'id' "kioskId", \
                                    station->'properties' "properties" \
                                 FROM indego, jsonb_array_elements(indego.data->'features') station \
                                 WHERE ((station->'properties'->>'name' ILIKE '%%%(search)s%%' \
                                    OR station->'properties'->>'addressStreet' ILIKE '%%%(search)s%%') \
                                    AND added = %(added)s) \
                                 ORDER BY indego.added DESC;"""
                    cur.execute(query, {"search": AsIs(str(search)), "added": added})

            else:

                search  = re.sub(r'[^a-zA-Z0-9\&\,\. ]', '', search)
                query   = """SELECT station->'properties'->'id' "kioskId", \
                                station->'properties' "properties" \
                             FROM indego, jsonb_array_elements(indego.data->'features') station \
                             WHERE ((station->'properties'->>'name' ILIKE '%%%(search)s%%' \
                                OR station->'properties'->>'addressStreet' ILIKE '%%%(search)s%%') \
                                AND added = %(added)s) \
                             ORDER BY indego.added DESC;"""
                cur.execute(query, {"search": AsIs(search), "added": added})

            results = cur.fetchall()

        return results

    # Print (and return) any exception
    except Exception as e:
        print(f"\n\nfind_stations:\n{e}\n\n")
        return e

    # Close the database connection
    finally:
        conn.close()

"""
Define a function to retrieve historical bicycle availability data from PostgreSQL
"""
def fetch_chart_data(id=None):

    # Bail if the station ID given seems non-existent
    if not id or not isinstance(id, int) or not find_stations(id):
        return None

    # Proceed with trying to get historical bicycle availability
    try:

        # Create a query to get timestamps, along with bicycles available at that time, for a specific station kioskId
        query       = """SELECT EXTRACT(EPOCH FROM added)*1000 "when", \
                        station->'properties'->'bikesAvailable' "bikesAvailable" \
                     FROM indego, jsonb_array_elements(data->'features') station \
                     WHERE added > NOW() - INTERVAL '1 MONTH' \
                     AND station->'properties'->>'kioskId' = '%s' \
                     ORDER BY added ASC;"""

        # Connect to the database to get chart data
        conn        = dbc()
        with conn.cursor() as cur:

            # Execute the query using the stations kioskId that we want availability information for
            cur.execute(query, (id,))
            result  = cur.fetchall()

        # Return the query results
        return result

    # Print (and return) any exceptions
    except Exception as e:
        print(f"\n\nfetch_chart_data:\n{e}\n\n")
        return e

    # Close the database connection
    finally:
        conn.close()

"""
Define primary route that displays search results and lists stations, from the database
By default, all stations are shown, from the latest JSONB row added to the database that is not NULL
"""
@app.route('/', methods=['GET'])
def index(search=None, emoji=False):

    # Display stations with bicycle emojis when using the punycode URL
    if request.headers['Host'] and 'xn--h78h' in request.headers['Host']:
        emoji       = True

    # Get the stations based on any search input
    results         = find_stations(search)

    if results:
        code        = 200
        stations    = dict(results)

    # If no stations were found, respond using a 404
    else:
        code        = 404
        stations    = None

    # Render the Jinja2 template listing which ever stations
    return render_template('index.html.j2', stations=stations, emoji=emoji), code


"""
Define Flask search route to allow searching stations
They are then displayed via the index() function and its Jinja2 template
"""
@app.route('/search', methods=['GET'])
@app.route('/search/', methods=['GET'])
@app.route('/search/<path:search>', methods=['GET'])
def search_stations(search=None):
    return index(search=search)


"""
Define Flask route that allows searching via the POST method search form (on the Jinja2 template index page)
This simply redirects to /search/<search_query> and handled by the above (search_stations) function which passes it off to the index() function
"""
@app.route('/search', methods=['POST'])
def search_form():
    return redirect(url_for('search_stations', search=request.form['search']))


"""
Define Flask route for showing charts of historical bicycle availability for stations
This is usually shown within a pop-up, from the main index page
"""
@app.route('/chart/<string:chart_string>', methods=['GET'])
def chart_station(chart_string=None):

    # Find stations based on route search string
    chart_results       = find_stations(chart_string)

    # Assuming any stations were found, respond using a 200
    if chart_results:
        chart_stations  = chart_results
        code            = 200

    # If no stations were found, respond using a 404
    else:
        chart_stations  = None
        code            = 404

    # Render the Jinja2 template to show charts (which are mostly server-generated JavaScript, using the functions below)
    return render_template('chart.html.j2', chart_stations=chart_stations, chart_string=chart_string), code


"""
Define Flask route for the front-end JavaScript necessary for charts
"""
@app.route('/chartjs/<string:chartjs_string>.js', methods=['GET'])
def chartjs_station(chartjs_string=None):

    # Find stations based on route search string
    chartjs_results         = find_stations(chartjs_string)

    # Assuming any stations were found, respond using a 200
    if chartjs_results:
        chartjs_stations    = chartjs_results
        code                = 200

    # If no stations were found, respond using a 404
    else:
        chartjs_stations    = None
        code                = 404

    """
    Render the chartjs Jinja2 template as JavaScript
    This route is usually only included from the /chart/ route with a station kioskID in a pop-up from the main page
    This can be called with a string to show multiple stations (each station found will have its own chart on one page, which can be resource-intensive with many stations)
    """
    chartjs_template        = render_template('chart.js.j2', chartjs_stations=chartjs_stations), code
    chartjs_response        = make_response(chartjs_template)
    chartjs_response.headers['Content-Type'] = 'text/javascript'
    return chartjs_response


"""
Define Flask route for generating the JavaScript using PostgreSQL data for charts
"""
@app.route('/chartdata/<int:id>.js', methods=['GET'])
def chartdata_station(id=None):

    # Find single station based on route kioskId (cannot be a string)
    chartdata_result        = find_stations(id)

    # Respond using a 200 if the one station was found and has historical data
    if chartdata_result:
        chartdata_station   = chartdata_result
        chart_data          = fetch_chart_data(id)
        code                = 200

    # Otherwise, respond using a 404
    else:
        chartdata_station   = None
        chart_data          = None
        code                = 404

    """
    Render the chartdata Jinja2 template as JavaScript
    This route is called by the chart_station function (/chart/ route)
    It provides a JavaScript list of timestamps along with the number of bicycles available at that time for a specific station using historical PostgreSQL data
    """
    chartdata_template      = render_template('chartdata.js.j2', station=chartdata_station, chart_data=chart_data), code
    chartdata_response      = make_response(chartdata_template)
    chartdata_response.headers['Content-Type'] = 'text/javascript'
    return chartdata_response


"""
Define Flask function to serve some static content
"""
@app.route('/icon.png', methods=['GET'])
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])
