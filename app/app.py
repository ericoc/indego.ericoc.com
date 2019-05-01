from flask import Flask, render_template, send_from_directory, request, make_response, url_for, redirect
from indego import Indego
import pymysql
import psycopg2
import db_creds_ro
import re

app = Flask(__name__)

def find_stations(search=None):

    if search and not isinstance(search, int):
        search = re.sub(r'[^a-zA-Z0-9\&\,\. ]', '', search)

    indego = Indego()
    station_results = indego.get_stations(search)
    return station_results


def fetch_chart_data(fetch_data_id=None):

    if not fetch_data_id or not isinstance(fetch_data_id, int) or not find_stations(fetch_data_id):
        return None

    try:

        fetch_data_query = "SELECT UNIX_TIMESTAMP(`added`)*1000 AS `added`, `bikesAvailable` FROM `data` WHERE `kioskId` = %s AND `added` > NOW() - INTERVAL 1 MONTH ORDER BY `added` ASC"
        chart_dbh = pymysql.connect(host=db_creds_ro.db_creds_ro['host'], user=db_creds_ro.db_creds_ro['user'], passwd=db_creds_ro.db_creds_ro['passwd'], db=db_creds_ro.db_creds_ro['db'])

        with chart_dbh.cursor() as chart_dbc:
            chart_dbc.execute(fetch_data_query, (fetch_data_id))
            chart_db_result = chart_dbc.fetchall()

        chart_dbh.close()
        return chart_db_result

    except Exception:
        return None


def fetch_pchart_data(fetch_data_id=None):

    if not fetch_data_id or not isinstance(fetch_data_id, int) or not find_stations(fetch_data_id):
        return None

    try:

        fetch_data_query = (SELECT EXTRACT(EPOCH FROM added)::integer "added",  station->'properties'->'bikesAvailable' "bikesAvailable" FROM indego, jsonb_array_elements(data->'features') station WHERE station->'properties'->>'kioskId' = %s added > NOW() - INTERVAL '1 MONTH';)
        chart_dbh = psycopg2.connect(user='indego', password=db_creds_rw.db_creds_rw['passwd'], host='localhost', port='5432', database='indego')

        with chart_dbh.cursor() as chart_dbc:
            chart_dbc.execute(fetch_data_query, (fetch_data_id))
            chart_db_result = chart_dbc.fetchall()

        chart_dbh.close()
        return chart_db_result

    except Exception:
        return None


@app.route('/')
def index(search_string=None, emoji=False):

    if request.headers['Host']:
        if request.headers['Host'] == 'xn--h78h.ericoc.com' or request.headers['Host'] == 'xn--h78h.ericoc.com.':
            emoji = True

    indego_stations = find_stations(search_string)

    if indego_stations and len(indego_stations) > 0:
        code = 200
    else:
        code = 404

    return render_template('index.html.j2', indego_stations=indego_stations, emoji=emoji), code

@app.route('/search/<search_string>')
def search_stations(search_string=None):
    return index(search_string=search_string)

@app.route('/search')
def search_form():
    return redirect(url_for('search_stations', search_string=request.args.get('search')))

@app.route('/chart/<chart_string>')
def chart_station(chart_string=None):

    chart_results = find_stations(chart_string)

    if chart_results:
            chart_stations = list(chart_results.values())
            code = 200
    else:
            chart_stations = None
            code = 404

    return render_template('chart.html.j2', chart_stations=chart_stations, chart_string=chart_string), code


@app.route('/chartjs/<chartjs_id>')
def chartjs_station(chartjs_id=None):

    chartjs_results = find_stations(chartjs_id)

    if chartjs_results:
        chartjs_stations = list(chartjs_results.values())
        code = 200
    else:
        chartjs_stations = None
        code = 404

    chartjs_template = render_template('chart.js.j2', chartjs_stations=chartjs_stations), code
    chartjs_response = make_response(chartjs_template)
    chartjs_response.headers['Content-Type'] = 'text/javascript'
    return chartjs_response


@app.route('/chartdata/<int:chartdata_id>')
def chartdata_station(chartdata_id=None):

    chartdata_result = find_stations(chartdata_id)
    chartdata_station = list(chartdata_result.values())
    chart_data = fetch_chart_data(chartdata_id)

    if chart_data and len(chart_data) > 0:
        code = 200
    else:
        chartdata_station = None
        chart_data = None
        code = 404

    chartdata_template = render_template('chartdata.js.j2', chartdata_station=chartdata_station, chart_data=chart_data), code
    chartdata_response = make_response(chartdata_template)
    chartdata_response.headers['Content-Type'] = 'text/javascript'
    return chartdata_response

@app.route('/pchartdata/<int:chartdata_id>')
def pchartdata_station(chartdata_id=None):

    chartdata_result = find_stations(chartdata_id)
    chartdata_station = list(chartdata_result.values())
    chart_data = fetch_pchart_data(chartdata_id)

    print(chart_data)

    if chart_data and len(chart_data) > 0:
        code = 200
    else:
        chartdata_station = None
        chart_data = None
        code = 404

    chartdata_template = render_template('chartdata.js.j2', chartdata_station=chartdata_station, chart_data=chart_data), code
    chartdata_response = make_response(chartdata_template)
    chartdata_response.headers['Content-Type'] = 'text/javascript'
    return chartdata_response

@app.route('/icon.png')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])

if __name__ == "__main__":
    app.run()
