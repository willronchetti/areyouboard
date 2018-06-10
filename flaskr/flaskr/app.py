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

    dataset = Dataset()

    originalState = 0
    queryName = []

    # State variable is 2 - do an advanced search
    if json.loads(request.form['state'])['state'] == 2:
        originalState = 2
        d = request.form['advancedVal']
        data = json.loads(d)

        # If no difficulty specified, give a medium difficulty
        if not data[1]["difficulty"]:
            complexity = (2,3)
        else:
            complexity = data[1]["difficulty"]

        related_games = doAdvancedSearch(Dataset(), data[1]["players"], data[1]["time"], complexity, data[1]['mechanics'], data[1]["category"], data[1]['other_games'], data[1]['not_category'], data[1]['not_mechanic'])[1]

    # Simple search
    else:
        originalState = 1
        d = request.form["jsonval"]
        data = json.loads(d)
        queryName = data[1]["name"]
        if len(data[1]['name']) == 1:
            related_games = getRelatedGames(dataset, data[1]["name"][0].upper())
        else:
            games = []
            for game in data[1]["name"]:
                games.append(game.upper())
            related_games = getRelatedMultipleGames(dataset, games)[1]

    top30_related_games = related_games[:30]

    # Get the original vectors from the dataset for the most similar games
    related_games_info = []
    for game_tup in top30_related_games:
        game_name = game_tup[0]
        game_data = dataset.games[game_name]
        related_games_info.append([game_data, game_tup[1]])
    return render_template('search.html', state=originalState, query = queryName, results=related_games_info)


if __name__ == "__main__":
    print("Flask app running at http://0.0.0.0:5000")
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
