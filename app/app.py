import re
import secrets
import datetime
import pytz
import psycopg2
from psycopg2.extensions import AsIs
from flask import Flask, flash, make_response, redirect, render_template, request, send_from_directory, url_for

"""
Initialize
"""
app = Flask(__name__)
app.config.from_pyfile('config.py')

if __name__ == '__main__':
    app.run(debug=True)

# Get database classes
#import models

"""
Error handling
"""
@app.errorhandler(400)
def bad_request(message):
    return error(message=message, category='fatal', code=400)

@app.errorhandler(404)
def page_not_found(message):
    return error(message=message, code=404)

@app.errorhandler(500)
def internal_server_error(message):
    return error(message=message, category='fatal', code=500)

@app.errorhandler(501)
def method_not_implemented(message):
    return error(message=message, category='fatal', code=501)

@app.errorhandler(503)
def service_unavailable(message):
    return error(message=message, category='fatal', code=503)

def error(message='Sorry, but there was an error. Please try again or come back later.', category='warn', code=500):
    flash(message, category)
    return make_response(render_template('index.html.j2'), code)


"""
Define a function to connect to the PostgreSQL database (using read-only credentials)
"""
def dbc(username=secrets.db_creds['username'], password=secrets.db_creds['password']):

    try:
        print('dbc connecting')
        return psycopg2.connect(
                                user        = username,
                                password    = password,
                                host        = '127.0.0.1',
                                port        = 5432,
                                database    = 'indego'
                )
    except Exception as e:
        print(f"\n\ndbc:\n{e}\n\n")
        return e


"""
Define a function to find stations, at whatever time, based on whatever search string
"""
def find_stations(added=None, search=None, field=None):

    try:
        conn = dbc()
        with conn.cursor() as cur:

            # If no "added" time was given, create/run query to find the latest database added time that does not have null data
            if not added:
                added_query     = """SELECT MAX(added) FROM indego WHERE data IS NOT NULL;"""
                cur.execute(added_query)
                latest_added    = cur.fetchone()
                added           = latest_added[0]

            # Return all stations by default
            if not search and not field:
                default_query   = """SELECT station->'properties'->'id' "kioskId", station->'properties' "properties" \
                                     FROM indego, jsonb_array_elements(indego.data->'features') station \
                                     WHERE added = %s \
                                     ORDER BY indego.added DESC;"""
                cur.execute(default_query, (added,))
                default_results = cur.fetchall()
                return default_results

            # Perform any search requested
            if search:

                # Check for numeric search query indicative of kiosk ID or zip/postal code (4 or 5 digits)
                if not field and search.isnumeric():
                    length  = len(search)

                    if length == 4:
                        field   = 'kioskId'
                    elif length == 5:
                        field   = 'addressZipCode'

                # Try to match and return rows with specific field values, if requested
                if field:
                    field_query = f"""SELECT station->'properties'->'id' "kioskId", \
                                      station->'properties' "properties" \
                                      FROM indego, jsonb_array_elements(indego.data->'features') station \
                                      WHERE station->'properties'->>'{field}' = '%(search)s' \
                                      AND added = %(added)s \
                                      ORDER BY indego.added DESC;"""
                    cur.execute(field_query, {"search": int(search), "added": added})
                    field_results = cur.fetchall()
                    if field_results:
                        return field_results

                # Finally, match and return rows using a text search on name and addressStreet fields
                search_query    = """SELECT station->'properties'->'id' "kioskId", \
                                     station->'properties' "properties" \
                                     FROM indego, jsonb_array_elements(indego.data->'features') station \
                                     WHERE ((station->'properties'->>'name' ILIKE '%%%(search)s%%' \
                                     OR station->'properties'->>'addressStreet' ILIKE '%%%(search)s%%') \
                                     AND added = %(added)s) \
                                     ORDER BY indego.added DESC;"""
                cur.execute(search_query, {"search": AsIs(re.sub(r'[^a-zA-Z0-9\&\,\. ]', '', str(search))), "added": added})
                search_results  = cur.fetchall()
                return search_results

            return None

    # Print any exception, and return None
    except Exception as e:
        print(f"\n\nfind_stations:\n{e}\n\n")
        return None

    # Close the database connection
    finally:
        print('closing: ', conn)
        conn.close()

"""
Define a function to retrieve historical bicycle availability data from PostgreSQL
"""
def fetch_chart_data(id=None):

    # Bail if the station ID given seems non-existent
    if not id or not isinstance(id, int) or not find_stations(search=id, field='kioskId'):
        return None

    try:

        # Connect to the database to create and execute a query for chart data for a single station ID
        conn = dbc()
        with conn.cursor() as cur:
            query   = """SELECT EXTRACT(EPOCH FROM added)*1000 "when", \
                         station->'properties'->'bikesAvailable' "bikesAvailable" \
                         FROM indego, jsonb_array_elements(data->'features') station \
                         WHERE added > NOW() - INTERVAL '1 MONTH' \
                         AND station->'properties'->>'kioskId' = '%s' \
                         ORDER BY added ASC;"""
            cur.execute(query, (id,))
            result  = cur.fetchall()
        return result

    # Print (and return) any exceptions
    except Exception as e:
        print(f"\n\nfetch_chart_data:\n{e}\n\n")
        return e

    # Close the database connection
    finally:
        print('closing: ', conn)
        conn.close()

"""
Define primary Flask web routes to allow searching/displaying mapped stations, from the latest row in the database
"""
@app.route('/', methods=['GET'])
def index():
    return search_stations(search=None)

@app.route('/search', methods=['GET'])
@app.route('/search/', methods=['GET'])
@app.route('/search/<path:search>', methods=['GET'])
def search_stations(search=None, googlemaps_api_key=secrets.googlemaps_api_key):

    # Connect to the database and get the latest added time
    conn = dbc()
    with conn.cursor() as cur:
        query   = """SELECT MAX(added) FROM indego WHERE data IS NOT NULL;"""
        cur.execute(query)
        results = cur.fetchone()
        added   = results[0]
    print('closing: ', conn)
    conn.close()

    print(f"added: {added}")

    # Get results and respond using a 404 if no stations were found
    stations = find_stations(added=added, search=search)
    if stations:
        stations = dict(stations)
        r   = make_response(
                render_template('index.html.j2',
                    added               = added.astimezone(pytz.timezone('US/Eastern')),
                    stations            = stations,
                    googlemaps_api_key  = googlemaps_api_key
            )
        )
        r.headers.set('X-Station-Count', len(stations))
        return r

    return page_not_found('Sorry, but no stations were found!')


"""
Define Flask route that allows searching via the POST method search form
This redirects to /search/<search_query> and handled by the above (search_stations) function
"""
@app.route('/search', methods=['POST'])
def search_form():
    return redirect(url_for('search_stations', search=request.form['search']))


"""
Define Flask route for showing charts of historical bicycle availability for stations
This is usually shown within a pop-up for a single station, from the main index page
Also works visiting /chart/<search string> (i.e. /chart/Broad) though not obvious
"""
@app.route('/chart/<string:chart_string>', methods=['GET'])
def chart_station(chart_string=None):

    chart_results = find_stations(search=chart_string)
    if chart_results:
        return render_template('chart.html.j2',
                                    chart_stations  = chart_results,
                                    chart_string    = chart_string
                              )

    return page_not_found('Sorry, but no stations were found!')


"""
Define Flask route for the front-end JavaScript necessary for charts
"""
@app.route('/chartjs/<string:chartjs_string>.js', methods=['GET'])
def chartjs_station(chartjs_string=None):

    chartjs_results = find_stations(search=chartjs_string)
    if chartjs_results:
        r = make_response(render_template('chart.js.j2', chartjs_stations=chartjs_results))
        r.headers['Content-Type'] = 'text/javascript'
        return r

    return page_not_found('Sorry, but no stations were found!')


"""
Define Flask route for generating the JavaScript using PostgreSQL data for charts, for a single station
"""
@app.route('/chartdata/<int:id>.js', methods=['GET'])
def chartdata_station(id=None):

    chartdata_result = find_stations(search=id, field='kioskId')
    if chartdata_result[0][1]['kioskId'] == id:
        r   = make_response(
                render_template('chartdata.js.j2',
                                    station     = chartdata_result[0][1],
                                    chart_data  = fetch_chart_data(id)
                                )
            )
        r.headers['Content-Type'] = 'text/javascript'
        return r

    return page_not_found('Sorry, but no stations were found!')


"""
Define Flask function to serve some static content
"""
@app.route('/favicon.ico', methods=['GET'])
@app.route('/icon.png', methods=['GET'])
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])
