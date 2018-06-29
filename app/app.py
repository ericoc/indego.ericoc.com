from flask import Flask, render_template, send_from_directory, request
from indego import Indego

app = Flask(__name__)

def jawn(search_string=None, emoji=False):

    indego = Indego()
    search_results = indego.get_stations(search_string)

    return render_template('index.html.j2', indego_stations=search_results, emoji=emoji)

@app.route('/')
def index():
    return jawn()

@app.route('/search/<search_string>')
def search_stations(search_string):
    return jawn(search_string)

@app.route('/favicon.ico')
@app.route('/icon.png')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])

if __name__ == "__main__":
    app.run()
