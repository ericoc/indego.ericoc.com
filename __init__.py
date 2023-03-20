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
@app.errorhandler(400)
def bad_request(message):
    """400 error"""
    return error(message=message, category='fatal', code=400)


@app.errorhandler(404)
def page_not_found(message):
    """404 error"""
    return error(message=message, code=404)


@app.errorhandler(500)
def internal_server_error(message):
    """500 error"""
    return error(message=message, category='fatal', code=500)


@app.errorhandler(501)
def method_not_implemented(message):
    """501 error"""
    return error(message=message, category='fatal', code=501)


@app.errorhandler(503)
def service_unavailable(message):
    """503 error"""
    return error(message=message, category='fatal', code=503)


def error(message=None, category='warn', code=500):
    """Handle errors with template"""
    if message is None:
        message = 'Sorry, but there was an error. ' \
                  'Please try again or come back later.'
    flash(message, category)
    return render_template('index.html.j2'), code


@app.before_request
def pre():
    """Get latest station added time, and current time, before request"""
    g.latest_added = _latest_added()
    g.now = datetime.now()


@app.context_processor
def injects():
    """Variables available to all templates"""
    return {}


def _latest_added():
    """Find latest added station timestamp where data is not null"""
    return db_session.query(
        func.max(Indego.added)
    ).filter(
        Indego.data is not None
    ).first()[0]


def _find_stations(search=None, field=None):
    """Allow searching stations from the latest database row"""

    base_query = db_session.query(
        text("station->'properties' \"properties\"")
    ).select_from(
        Indego,
        func.jsonb_array_elements(
            Indego.data['features']
        ).alias('station')
    ).filter_by(
        added=g.latest_added
    )
    final_query = None
    
    # Perform any search requested
    if search:

        # Check for numeric search query,
        #   indicative of kiosk ID or zip/postal code (4 or 5 digits)
        if not field and search.isnumeric():
            length = len(search)

            if length == 4:
                field = 'kioskId'

            if length == 5:
                field = 'addressZipCode'

        # Search specific field values, if requested
        if field:
            final_query = base_query.filter(
                text(f"station->'properties'->>'{field}' = '{search}'")
            )

        # Search the name and addressStreet fields for the string
        else:
            final_query = base_query.filter(
                or_(text(
                    f"station->'properties'->>'name' ILIKE '%%{search}%%'"
                ), text(
                    f"station->'properties'->>'addressStreet' ILIKE '%%{search}%%'")
                )
            )

    # Last resort is to return all stations
    if not final_query:
        final_query = base_query
    return final_query.all()


@app.route('/', methods=['GET'])
def index():
    """Allow searching stations from the latest database row"""
    return search_stations(search=None)


@app.route('/search', methods=['POST'])
def search_form():
    """Search form"""
    return redirect(url_for('search_stations', search=request.form['search']))


@app.route('/search', methods=['GET'])
@app.route('/search/', methods=['GET'])
@app.route('/search/<path:search>', methods=['GET'])
def search_stations(search=None):
    """Search stations"""

    results = _find_stations(search=search)
    if results:

        stations = []
        for result in results:
            for station in result:
                stations.append(station)

        timezone = pytz.timezone('US/Eastern')
        added_web = g.latest_added.astimezone(timezone)
        added_since = g.now.astimezone(timezone) - added_web
        resp = make_response(
                render_template(
                    'index.html.j2',
                    added_since=added_since, added_web=added_web,
                    gmaps_api_key=app.config['GMAPS_API_KEY'],
                    search=search, stations=stations
                )
            )
        resp.headers.set('X-Station-Count', len(stations))
        return resp

    return page_not_found('Sorry, but no stations were found!')


@app.route('/chart/<string:chart_string>', methods=['GET'])
def chart_station(chart_string=None):
    """
    Show charts of historical bicycle availability for stations
    Shown within pop-up for a single station, from the main index page
    Also works at /chart/<search string> (i.e. /chart/Broad) though not obvious
    """
    chart_results = _find_stations(search=chart_string)
    chart_stations = []
    for chart_result in chart_results:
        for station in chart_result:
            chart_stations.append(station)

    if chart_stations:
        return render_template('chart.html.j2',
                               chart_stations=chart_stations,
                               chart_string=chart_string)

    return page_not_found('Sorry, but no stations were found!')


@app.route('/chartjs/<string:chartjs_string>.js', methods=['GET'])
def chartjs_station(chartjs_string=None):
    """Front-end JavaScript necessary for charts"""
    chartjs_results = _find_stations(search=chartjs_string)
    chartjs_stations = []
    for chartjs_result in chartjs_results:
        for station in chartjs_result:
            chartjs_stations.append(station)

    if chartjs_stations:
        resp = make_response(
                render_template(
                    'chart.js.j2',
                    chartjs_stations=chartjs_stations
                )
            )
        resp.headers['Content-Type'] = 'text/javascript'
        return resp

    return page_not_found('Sorry, but no stations were found!')


@app.route('/chartdata/<int:id>.js', methods=['GET'])
def chartdata_station(id=None):
    """Generate JavaScript using PostgreSQL data for charts, for one station"""
    try:
        chartdata_result = _find_stations(search=id, field='kioskId')[0][0]
    except IndexError:
        chartdata_result = {}
        chartdata_result['kioskId'] = None

    if chartdata_result['kioskId'] == id:
        resp = make_response(
                render_template('chartdata.js.j2',
                                station=chartdata_result,
                                chart_data=_fetch_chart_data(id)
                                )
                            )
        resp.headers['Content-Type'] = 'text/javascript'
        return resp

    return page_not_found('Sorry, but no stations were found!')


def _fetch_chart_data(id=None):
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
        text(f"station->'properties'->>'kioskId' = '{id}'")
    ).order_by('added').all()


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
