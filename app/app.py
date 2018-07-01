from flask import Flask, render_template, send_from_directory, request, make_response, url_for
from indego import Indego
import _mysql
import db_creds

app = Flask(__name__)

def check_kiosk_id(kiosk_id=None):

    indego = Indego()
    find_kiosk_id = indego.get_stations(kiosk_id)

    if find_kiosk_id and len(find_kiosk_id) >= 1:
        return find_kiosk_id
    else:
        return None


def home(search_string=None, emoji=False):

    indego = Indego()
    search_results = indego.get_stations(search_string)

    return render_template('index.html.j2', indego_stations=search_results, emoji=emoji)


def fetch_chart_data(fetch_data_id):

    if not fetch_data_id or not len(fetch_data_id) == 4 or not check_kiosk_id(fetch_data_id):
        return None

    fetch_data_query = "SELECT UNIX_TIMESTAMP(`added`)*1000 AS `added`, `bikesAvailable` FROM `data` WHERE `kioskId` = " + fetch_data_id + " AND `added` > NOW() - INTERVAL 1 MONTH ORDER BY `added` ASC;"
    chart_db = _mysql.connect(host=db_creds.db_creds['host'], user=db_creds.db_creds['user'], passwd=db_creds.db_creds['passwd'], db=db_creds.db_creds['db'])
    chart_db.query(fetch_data_query)
    chart_db_result = chart_db.store_result().fetch_row(how=1, maxrows=0)
    chart_db = None;
    return chart_db_result;


@app.route('/')
def index():
    return home()

@app.route('/search/<search_string>')
def search_stations(search_string=None):
    return home(search_string)

@app.route('/chart/<chart_string>')
def chart_station(chart_string=None):

    chart_results = check_kiosk_id(chart_string)

    if chart_results:
            chart_stations = list(chart_results.values())
            code = 200
    else:
            chart_stations = None
            code = 404

    return render_template('chart.html.j2', chart_stations=chart_stations, chart_string=chart_string), code


@app.route('/chartjs/<chartjs_id>')
def chartjs_station(chartjs_id=None):

    chartjs_results = check_kiosk_id(chartjs_id)

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


@app.route('/chartdata/<chartdata_id>')
def chartdata_station(chartdata_id=None):

    if not chartdata_id or not len(chartdata_id) == 4:
        chartdata_result = None
    else:
        chartdata_result = check_kiosk_id(chartdata_id)

    if chartdata_result:
        chartdata_station = list(chartdata_result.values())
        chart_data = fetch_chart_data(chartdata_id)
        code = 200
    else:
        chartdata_station = None
        chart_data = None
        code = 404

    chartdata_response = render_template('chartdata.js.j2', chartdata_station=chartdata_station, chart_data=chart_data), code
    response = make_response(chartdata_response)
    response.headers['Content-Type'] = 'text/javascript'
    return response


@app.route('/favicon.ico')
@app.route('/icon.png')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])

if __name__ == "__main__":
    app.run()
