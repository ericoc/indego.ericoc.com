from flask import Flask, render_template, send_from_directory, request, make_response, url_for, redirect
from indego import Indego
import psycopg2
import db_creds_ro
import re

"""
Initialize Flask app
"""
app = Flask(__name__)

"""
Define a function to find stations based on whatever search string
"""
def find_stations(search=None):

    # Assuming a number was not sent, remove any non-alphanumeric from the search string
    if search and not isinstance(search, int):
        search = re.sub(r'[^a-zA-Z0-9\&\,\. ]', '', search)

    # Instantiate Indego class and get station information from their API for stations based on the search string provided
    indego = Indego()
    station_results = indego.get_stations(search)
    return station_results


"""
Define a function to retrieve historical bicycle availability data from PostgreSQL
"""
def fetch_chart_data(fetch_data_id=None):

    # Bail if the station ID given seems non-existent
    if not fetch_data_id or not isinstance(fetch_data_id, int) or not find_stations(fetch_data_id):
        return None

    # Proceed with trying to get historical bicycle availability
    try:

        # Create a query to get timestamps along with bicycles available at that time from the database for a specific station kioskId
        fetch_data_query = """SELECT EXTRACT(EPOCH FROM added)*1000 "when", station->'properties'->'bikesAvailable' "bikesAvailable" FROM indego, jsonb_array_elements(data->'features') station WHERE added > NOW() - INTERVAL '1 MONTH' AND station->'properties'->>'kioskId' = '%s' ORDER BY added ASC;"""

        # Connect to the PostgreSQL database with read-only credentials
        chart_dbh = psycopg2.connect(user='indego', password=db_creds_ro.db_creds['passwd'], host='localhost', port='5432', database='indego')

        # Open a database cursor
        with chart_dbh.cursor() as chart_dbc:

            # Execute the query using the stations kioskId that we want availability information for
            chart_dbc.execute(fetch_data_query, (fetch_data_id,))
            chart_db_result = chart_dbc.fetchall()

        # Close the database connection and return the query results
        chart_dbh.close()
        return chart_db_result

    # Bail on any errors
    except:
        return None


"""
Define primary route that displays search results and lists stations
By default, all stations are shown
The search_stations function below refers back to this function when searching for stations
"""
@app.route('/', methods=['GET'])
def index(search_string=None, emoji=False):

    # Display stations with bicycle emojis when using the punycode URL
    if request.headers['Host'] and 'xn--h78h' in request.headers['Host']:
        emoji = True

    # Get which ever stations and all of their information so that they can be displayed
    indego_stations = find_stations(search_string)

    # Assuming any stations were found, respond using a 200
    if indego_stations and len(indego_stations) > 0:
        code = 200

    # If no stations were found, respond using a 404
    else:
        code = 404

    # Render the Jinja2 template listing which ever stations
    return render_template('index.html.j2', indego_stations=indego_stations, emoji=emoji), code


"""
Define NEW WIP route that displays search results and lists stations, from the database, rather than making a request to the Indego API
By default, all stations are shown, from the latest JSONB row added to the database that is not NULL
TODO: Search is broken with this - I need to parse search parameters more sanely some how to make it work right, WIP
"""
@app.route('/new', methods=['GET'])
def new(search_string=None, emoji=False):

    # Display stations with bicycle emojis when using the punycode URL
    if request.headers['Host'] and 'xn--h78h' in request.headers['Host']:
        emoji = True

    # Connect to the PostgreSQL database with read-only credentials
    dbh = psycopg2.connect(user=db_creds_ro.db_creds['user'], password=db_creds_ro.db_creds['passwd'], host='localhost', port='5432', database='indego')

    # Create a query to find the latest database entry that is not null
    latest_added_query  = """SELECT MAX(added) FROM indego WHERE data IS NOT NULL;"""

    # Create a query to get latest stations API results from the database
    latest_data_query   = """SELECT station->'properties'->'id' "kioskId", station->'properties' "properties"   \
                            FROM indego, jsonb_array_elements(indego.data->'features') station  \
                            WHERE added = %s \
                            ORDER BY indego.added DESC;"""

    # Open a database cursor
    with dbh.cursor() as dbc:

        # Get the latest added data time
        dbc.execute(latest_added_query)
        latest_added    = dbc.fetchone()
        added           = latest_added[0]

        # Use the latest added data time to get the latest station data
        dbc.execute(latest_data_query, (added,))
        indego_stations = dbc.fetchall()

        # Close the database connection and return the query results
        dbh.close()

    # Assuming any stations were found, respond using a 200
    if indego_stations and len(indego_stations) > 0:
        code = 200

    # If no stations were found, respond using a 404
    else:
        code = 404
        added = datetime.datetime.now()

    # Render the Jinja2 template listing which ever stations
    return render_template('index.html.j2', indego_stations=dict(indego_stations), added=added, emoji=emoji), code


"""
Define Flask search route to allow searching stations
They are then displayed via the index() function and its Jinja2 template
"""
@app.route('/search/<path:search_string>', methods=['GET'])
def search_stations(search_string=None):
    return index(search_string=search_string)

"""
Define Flask route that allows searching via the POST method search form (on the Jinja2 template index page)
This simply redirects to /search/<search_query> and handled by the above (search_stations) function which passes it off to the index() function
"""
@app.route('/search', methods=['POST'])
def search_form():
    return redirect(url_for('search_stations', search_string=request.form['search']))


"""
Define Flask route for showing charts of historical bicycle availability for stations
This is usually shown within a pop-up, from the main index page
"""
@app.route('/chart/<chart_string>', methods=['GET'])
def chart_station(chart_string=None):

    # Find stations based on route search string
    chart_results = find_stations(chart_string)

    # Assuming any stations were found, respond using a 200
    if chart_results:
            chart_stations = list(chart_results.values())
            code = 200

    # If no stations were found, respond using a 404
    else:
            chart_stations = None
            code = 404

    # Render the Jinja2 template to show charts (which are mostly server-generated JavaScript, using the functions below)
    return render_template('chart.html.j2', chart_stations=chart_stations, chart_string=chart_string), code


"""
Define Flask route for the front-end JavaScript necessary for charts
"""
@app.route('/chartjs/<chartjs_string>', methods=['GET'])
def chartjs_station(chartjs_string=None):

    # Find stations based on route search string
    chartjs_results = find_stations(chartjs_string)

    # Assuming any stations were found, respond using a 200
    if chartjs_results:
        chartjs_stations = list(chartjs_results.values())
        code = 200

    # If no stations were found, respond using a 404
    else:
        chartjs_stations = None
        code = 404

    """
    Render the chartjs Jinja2 template as JavaScript
    This route is usually only included from the /chart/ route with a station kioskID in a pop-up from the main page
    This can be called with a string to show multiple stations (each station found will have its own chart on one page, which can be resource-intensive with many stations)
    """
    chartjs_template = render_template('chart.js.j2', chartjs_stations=chartjs_stations), code
    chartjs_response = make_response(chartjs_template)
    chartjs_response.headers['Content-Type'] = 'text/javascript'
    return chartjs_response


"""
Define Flask route for generating the JavaScript using PostgreSQL data for charts
"""
@app.route('/chartdata/<int:chartdata_id>.js', methods=['GET'])
def chartdata_station(chartdata_id=None):

    # Find single station based on route kioskId (cannot be a string)
    chartdata_result = find_stations(chartdata_id)

    # Get all of the stations information
    chartdata_station = list(chartdata_result.values())

    # Fetch the stations historical data from PostgreSQL
    chart_data = fetch_chart_data(chartdata_id)

    # Respond using a 200 if the one station was found and has historical data
    if chartdata_result and len(chartdata_result) == 1 and chart_data and len(chart_data) > 0:
        code = 200

    # Otherwise, respond using a 404
    else:
        chartdata_station = None
        chart_data = None
        code = 404

    """
    Render the chartdata Jinja2 template as JavaScript
    This route is called by the chart_station function (/chart/ route)
    It provides a JavaScript list of timestamps along with the number of bicycles available at that time for a specific station using historical PostgreSQL data
    """
    chartdata_template = render_template('chartdata.js.j2', chartdata_station=chartdata_station, chart_data=chart_data), code
    chartdata_response = make_response(chartdata_template)
    chartdata_response.headers['Content-Type'] = 'text/javascript'
    return chartdata_response


"""
Define Flask function to serve some static content
"""
@app.route('/icon.png', methods=['GET'])
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])


"""
Run Flask
"""
if __name__ == "__main__":
    app.run()
