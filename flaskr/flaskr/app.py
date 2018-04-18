from flask import request, Flask, render_template
from flask_socketio import SocketIO
from string import Template
import sys
import json

from search import *

app = Flask(__name__)
socketio = SocketIO()

# Initialize app w/SocketIO
socketio.init_app(app)

global dataset

@app.route('/', methods=['GET', 'POST'])
def search():
    query = request.args.get('search')
    if not query:
        data = []
        output_message = ''
    else:
        output_message = "Your search: " + query
        data = range(5)
    return render_template('search.html')

@app.route('/receiveData', methods=['GET','POST'])
def getResults():
    print "Receiving Data"
    # data = request.get_json()

    d = request.form["jsonval"]
    data = json.loads(d)

    related_games = getRelatedGames(Dataset(), data[1]['name'].upper())
    return render_template('search.html', results=related_games)

if __name__ == "__main__":
    dataset = Dataset()
    print("Flask app running at http://0.0.0.0:5000")
    socketio.run(app, host="0.0.0.0", port=5000)
