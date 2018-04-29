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

# Loads the homepage with the results when called
@app.route('/receiveData', methods=['GET','POST'])
def getResults():

    print "Receiving Data"
    dataset = Dataset()

    originalState = 0
    queryName = ""

    # State variable is 2
    if (json.loads(request.form['state'])['state'] == 2):
        originalState = 2
        d = request.form['advancedVal']
        data = json.loads(d)
        print(data)

        # If no difficulty specified, give a medium difficulty
        if data[1]["difficulty"] == []:
            complexity = (2,3)
        else:
            complexity = data[1]["difficulty"]

        related_games = doAdvancedSearch(Dataset(), data[1]["players"], data[1]["time"],
            complexity, data[1]['mechanics'], data[1]["category"])[1]
    else:
        originalState = 1
        d = request.form["jsonval"]
        data = json.loads(d)
        if len(data[1]['name']) == 1:
            queryName = data[1]["name"]
            related_games = getRelatedGames(dataset, data[1]["name"][0].upper())
        else:
            games = []
            for game in data[1]["name"]:
                games.append(game.upper())
            related_games = getRelatedMultipleGames(dataset, games)[1]

    top10_related_games = related_games[:30]

    # Get the original vectors from the dataset for the most similar games
    related_games_info = []
    for game_tup in top10_related_games:
        game_name = game_tup[0]
        game_data = dataset.games[game_name]
        related_games_info.append([game_data, game_tup[1]])
    print(related_games_info)
    return render_template('search.html', state=originalState, query = queryName, results=related_games_info)

if __name__ == "__main__":
    print("Flask app running at http://0.0.0.0:5000")
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
