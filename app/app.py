import re
import secrets
import psycopg2
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
def dbc(username=secrets.db_creds['username'], password=secrets.db_creds['password']):
    try:
        return psycopg2.connect(
                                user        = username,
                                password    = password,
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
def find_stations(search=None, field=None):

    try:

        # Connect to the database
        conn = dbc()
        with conn.cursor() as cur:

            # Create a query to find the latest database row that is not null, to get the latest added data time
            added_query     = """SELECT MAX(added) FROM indego WHERE data IS NOT NULL;"""
            cur.execute(added_query)
            latest_added    = cur.fetchone()
            added           = latest_added[0]

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
        conn.close()

"""
Define primary route that displays and maps search results and lists stations, from the latest row in the database
"""
@app.route('/', methods=['GET'])
def index(stations=find_stations(), googlemaps_api_key=secrets.googlemaps_api_key):

    # Count results, or respond using a 404 if no stations were found
    if stations:
        code        = 200
        count       = len(stations)
        stations    = dict(stations)
    else:
        code        = 404
        count       = 0
        stations    = None

    # Return Jinja2 template listing stations, and HTTP header with the result count
    r   = make_response(
            render_template('index.html.j2',
                stations            = stations,
                googlemaps_api_key  = googlemaps_api_key
            ), code
        )
    r.headers.set('X-Station-Count', count)
    return r


"""
Define Flask search route to allow searching stations
They are then displayed via the index() function and its Jinja2 template
"""
@app.route('/search', methods=['GET'])
@app.route('/search/', methods=['GET'])
@app.route('/search/<path:search>', methods=['GET'])
def search_stations(search=None):
    stations = find_stations(search=search)
    return index(stations=stations)

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

    # Find stations based on route search string and return any results using a 200 response, otherwise 404
    chart_results       = find_stations(search=chart_string)
    if chart_results:
        chart_stations  = chart_results
        code            = 200
    else:
        chart_stations  = None
        code            = 404

    return render_template('chart.html.j2',
                                chart_stations  = chart_stations,
                                chart_string    = chart_string
                          ), code


"""
Define Flask route for the front-end JavaScript necessary for charts
"""
@app.route('/chartjs/<string:chartjs_string>.js', methods=['GET'])
def chartjs_station(chartjs_string=None):

    # Find any stations based on route search string and respond using a 200, or 404 if none found
    chartjs_results         = find_stations(search=chartjs_string)
    if chartjs_results:
        chartjs_stations    = chartjs_results
        code                = 200
    else:
        chartjs_stations    = None
        code                = 404

    r   = make_response(render_template('chart.js.j2', chartjs_stations=chartjs_stations), code)
    r.headers['Content-Type'] = 'text/javascript'
    return r


"""
Define Flask route for generating the JavaScript using PostgreSQL data for charts, for a single station
"""
@app.route('/chartdata/<int:id>.js', methods=['GET'])
def chartdata_station(id=None):

    # Find single station based on route kioskId (cannot be a string)
    chartdata_result        = find_stations(search=id, field='kioskId')

    # Respond using a 200 if the one station was found and has historical data, otherwise 404
    if chartdata_result:
        chartdata_station   = chartdata_result[0][1]
        chart_data          = fetch_chart_data(id)
        code                = 200
    else:
        chartdata_station   = None
        chart_data          = None
        code                = 404

    r   = make_response(render_template('chartdata.js.j2', station=chartdata_station, chart_data=chart_data), code)
    r.headers['Content-Type'] = 'text/javascript'
    return r


"""
Define Flask function to serve some static content
"""
@app.route('/icon.png', methods=['GET'])
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])
