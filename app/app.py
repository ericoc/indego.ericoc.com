from flask import Flask, render_template, send_from_directory, request
from indego import Indego

app = Flask(__name__)


def jawn(search_string=None, emoji=False):

    indego = Indego()
    search_results = indego.get_stations(search_string)

    return render_template('index.html.j2', indego_stations=search_results, emoji=emoji)


def chart_jawn(kiosk_id=None):

    indego = Indego()
    find_station = indego.get_stations(kiosk_id)

    try:
        if find_station and len(find_station) > 0:
            code = 200
            station = find_station
        else:
            code = 404
            station = None
    except TypeError:
        code = 404
        station = None

    return render_template('chart.html.j2', station=station), code


@app.route('/')
def index():
    return jawn()

@app.route('/search/<search_string>')
def search_stations(search_string):
    return jawn(search_string)

@app.route('/chart/<chart_id>')
def chart_station(chart_id):
    return chart_jawn(kiosk_id=chart_id)

@app.route('/favicon.ico')
@app.route('/icon.png')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])

if __name__ == "__main__":
    app.run()
