from flask import Flask, render_template, send_from_directory, request, make_response
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


def chart_web(chart_string=None):

    if chart_string:
        chart_results = check_kiosk_id(chart_string)
    else:
        chart_results = None

    if chart_results:
            chart_stations = list(chart_results.values())
            code = 200
    else:
            chart_stations = None
            code = 404

    return render_template('chart.html.j2', chart_stations=chart_stations, chart_string=chart_string), code


def chartjs_web(kiosk_id=None):

    chartjs_kiosk = check_kiosk_id(kiosk_id)

    if chartjs_kiosk:
        indego_stations = list(chartjs_kiosk.values())
        code = 200
    else:
        indego_stations = None
        code = 404

    chartjs_response = render_template('chart.js.j2', indego_stations=indego_stations), code
    response = make_response(chartjs_response)
    response.headers['Content-Type'] = 'text/javascript'
    return response


def chartdata_web(kiosk_id=None):

    chartdata_kiosk = check_kiosk_id(kiosk_id)

    if chartdata_kiosk:
        indego_station = list(chartdata_kiosk.values())
        chart_data = fetch_chart_data(kiosk_id)
        code = 200
    else:
        indego_station = None
        chart_data = None
        code = 404

    chartdata_response = render_template('chart_data.js.j2', indego_station=indego_station, chart_data=chart_data), code
    response = make_response(chartdata_response)
    response.headers['Content-Type'] = 'text/javascript'
    return response


def fetch_chart_data(kiosk_id):

#    SELECT UNIX_TIMESTAMP(`added`)*1000 AS `added`, `bikesAvailable` FROM `data` WHERE `kioskId` = :kioskId AND `added` > NOW() - INTERVAL 1 MONTH ORDER BY `added` ASC;

    db = _mysql.connect(host=db_creds.db_creds['host'], user=db_creds.db_creds['user'], passwd=db_creds.db_creds['passwd'], db=db_creds.db_creds['db'])
    chart_query = "SELECT UNIX_TIMESTAMP(`added`)*1000 AS `added`, `bikesAvailable` FROM `data` WHERE `kioskId` = " + kiosk_id + " AND `added` > NOW() - INTERVAL 1 MONTH ORDER BY `added` ASC;"
    db.query(chart_query)
    result = db.store_result().fetch_row(how=1, maxrows=0)
    db = None;
    return result;

@app.route('/')
def index():
    return home()

@app.route('/search/<search_string>')
def search_stations(search_string):
    return home(search_string)

@app.route('/chart/<chart_string>')
def chart_station(chart_string):
    return chart_web(chart_string)

@app.route('/chartjs/<chartjs_id>')
def chartjs_station(chartjs_id):
    return chartjs_web(kiosk_id=chartjs_id)

@app.route('/chartdata/<chartdata_id>')
def chartdata_station(chartdata_id):
    return chartdata_web(kiosk_id=chartdata_id)

@app.route('/favicon.ico')
@app.route('/icon.png')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])

if __name__ == "__main__":
    app.run()
