"""
https://indego.ericoc.com
https://github.com/ericoc/indego.ericoc.com
__init__.py
"""
from datetime import datetime, timedelta
import pytz

from flask import Flask, flash, g, make_response, render_template, redirect, \
    request, send_from_directory, url_for
from sqlalchemy import extract, func, or_, text

from database import db_session
from models import Indego


# Flask
app = Flask(__name__)
app.config.from_pyfile('config.py')


# Error handlers
def _error(message='Sorry, but there was an error.', category='warn', code=500):
    """Handle errors with flash and response code"""
    flash(message, category)
    return render_template('index.html.j2'), code


@app.errorhandler(404)
def _page_not_found(message):
    """Page Not Found (404 error handler)"""
    return _error(message=message, code=404)


@app.before_request
def pre():
    """Get latest added time, and current time, before request"""
    g.latest_added = _latest_added()
    g.now = datetime.now()


def _latest_added():
    """Latest added timestamp where station data is not null"""
    return db_session.query(
        func.max(Indego.added)
    ).filter(
        Indego.data is not None
    ).first()[0]


def _fetch_chart_data(kiosk_id=None):
    """Retrieve historical bicycle availability data from PostgreSQL,
        to generate JavaScript chart data for a single station"""
    return db_session.query(
        (extract('epoch', Indego.added)*1000).label('added'),
        text("station->'properties'->>'bikesAvailable' \"bikesAvailable\"")
    ).select_from(
        Indego,
        func.jsonb_array_elements(
            Indego.data['features']
        ).alias('station')
    ).filter(
        Indego.data is not None,
        Indego.added >= g.now - timedelta(days=30),
        text(f"station->'properties'->>'kioskId' = '{kiosk_id}'")
    ).order_by('added').all()


def _find_stations(search=None, field=None):
    """Find stations from the latest added database row"""

    # Form base query to get stations from the JSON PostgreSQL data
    base_query = db_session.query(
        text("station->'properties' \"properties\"")
    ).select_from(
        Indego,
        func.jsonb_array_elements(Indego.data['features']).alias('station')
    ).filter_by(
        added=g.latest_added
    )
    final_query = base_query

    # Perform any search requested
    if search:
        final_query = base_query.filter(
            _station_filter(search=search, field=field)
        )

    # Execute the query
    results = final_query.all()

    # Create a stations list containing station dictionary items
    stations = []
    for result in results:
        for station in result:
            stations.append(station)

    # Return the list of station dictionaries
    return stations


def _station_filter(search=None, field=None):
    """Query filter to search stations"""

    # Get length of numeric searches
    if not field and search.isnumeric():
        length = len(search)

        # Treat four (4) digits as kioskID
        if length == 4:
            field = 'kioskId'

        # Treat five (5) digits as zip code
        if length == 5:
            field = 'addressZipCode'

    # Filter by a specific station field value, if requested
    if field:
        return text(f"station->'properties'->>'{field}' = '{search}'")

    # Search the name and addressStreet fields for the string
    return or_(
        text(f"station->'properties'->>'name' ILIKE '%%{search}%%'"),
        text(f"station->'properties'->>'addressStreet' ILIKE '%%{search}%%'")
    )


@app.route('/', methods=['GET'])
def index():
    """Main page returns all stations"""
    return search_stations(search=None)


@app.route('/search', methods=['POST'])
def search_form():
    """Search form"""
    return redirect(
        url_for('search_stations', search=request.form['search'])
    )


@app.route('/search', methods=['GET'])
@app.route('/search/', methods=['GET'])
@app.route('/search/<path:search>', methods=['GET'])
def search_stations(search=None):
    """Search stations"""
    stations = _find_stations(search=search)
    if stations:
        timezone = pytz.timezone('US/Eastern')
        added_web = g.latest_added.astimezone(timezone)
        added_since = g.now.astimezone(timezone) - added_web
        resp = make_response(
            render_template(
                'index.html.j2',
                added_since=added_since,
                added_web=added_web,
                gmaps_api_key=app.config['GMAPS_API_KEY'],
                stations=stations
            )
        )
        resp.headers.set('X-Station-Count', len(stations))
        return resp

    return _page_not_found('Sorry, but no stations were found!')


@app.route('/chart/<string:chart_string>', methods=['GET'])
def chart_station(chart_string=None):
    """
    Show charts of historical bicycle availability for stations
    Shown within pop-up for a single station, from the main index page
    Also works at /chart/<search string> (i.e. /chart/Broad) though not obvious
    """
    chart_stations = _find_stations(search=chart_string)
    if chart_stations:
        return render_template(
            'chart.html.j2',
            chart_stations=chart_stations,
            chart_string=chart_string
        )

    return _page_not_found('Sorry, but no stations were found!')


@app.route('/chartjs/<string:chartjs_string>.js', methods=['GET'])
def chartjs_station(chartjs_string=None):
    """JavaScript for a chart, or multiple charts"""
    chartjs_stations = _find_stations(search=chartjs_string)
    if chartjs_stations:
        resp = make_response(
            render_template(
                'chart.js.j2',
                chartjs_stations=chartjs_stations
            )
        )
        resp.headers['Content-Type'] = 'text/javascript'
        return resp

    return _page_not_found('Sorry, but no stations were found!')


@app.route('/chartdata/<int:kiosk_id>.js', methods=['GET'])
def chartdata_station(kiosk_id=None):
    """JavaScript using PostgreSQL data for charts, for one station"""
    chartdata_result = _find_stations(search=kiosk_id, field='kioskId')[0]
    if chartdata_result:
        resp = make_response(
            render_template(
                'chartdata.js.j2',
                station=chartdata_result,
                chart_data=_fetch_chart_data(kiosk_id=kiosk_id)
            )
        )
        resp.headers['Content-Type'] = 'text/javascript'
        return resp

    return _page_not_found('Sorry, but no stations were found!')


@app.route('/favicon.ico', methods=['GET'])
@app.route('/icon.png', methods=['GET'])
def static_from_root():
    """Static content"""
    return send_from_directory(app.static_folder, request.path[1:])


@app.teardown_appcontext
def shutdown_session(err=None):
    """Remove database session at request teardown"""
    db_session.remove()
    if err:
        raise err


if __name__ == '__main__':
    app.run()
