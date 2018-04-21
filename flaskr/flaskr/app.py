from flask import request, Flask, render_template
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from string import Template
import sys
import json

from search import *

app = Flask(__name__)
socketio = SocketIO()

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)

# Initialize app w/SocketIO
socketio.init_app(app)

# Loads the blank homepage
@app.route('/', methods=['GET', 'POST'])
def search():
    return render_template('search.html')

#Loads the homepage with the results when called
@app.route('/receiveData', methods=['GET','POST'])
def getResults():

    print "Receiving Data"
    dataset = Dataset()

    data = request.get_json()
    print(request.args)
    print('here')

    if (data == None):
        d = request.form["jsonval"]
        data = json.loads(d)

    related_games = []
    if ("name" in data[1]):
        related_games = getRelatedGames(Dataset(), data[1]["name"].upper())
    else:
        print(data[1]["players"])
        print(data[1]["age"])
        print(data[1]["time"])
        print(data[1]["difficulty"])
        print(data[1]["category"])
        related_games = doAdvancedSearch(Dataset(), data[1]["players"],
                    data[1]["age"], data[1]["time"], data[1]["difficulty"], data[1]["category"])[1]
    top10_related_games = related_games[:10]
    print(top10_related_games)
    # Get the original vectors from the dataset for the most similar games
    related_games_info = []
    for game_tup in top10_related_games:
        game_name = game_tup[0]
        game_data = dataset.games[game_name]
        related_games_info.append([game_data, game_tup[1]])
    print(related_games_info)
    return render_template('search.html', results=related_games_info)

if __name__ == "__main__":
    print("Flask app running at http://0.0.0.0:5000")
    socketio.run(app, host="0.0.0.0", port=5000)
