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

#Loads the blank homepage
@app.route('/', methods=['GET', 'POST'])
def search():
    return render_template('search.html')

#Loads the homepage with the results when called
@app.route('/receiveData', methods=['GET','POST'])
def getResults():
    print "Receiving Data"
    # data = request.get_json()

    d = request.form["jsonval"]
    data = json.loads(d)

    related_games = getRelatedGames(Dataset(), data[1]['name'].upper())
    top10_related_games = related_games[0:10]
    print(top10_related_games)

    #get the original vectors from the dataset for the most similar games
    related_games_info = []
    for game_tup in top10_related_games:
        game_name = game_tup[0]
        game_data = dataset.games[game_name]
            #game data is some abstract object with .fields as the columns
        related_games_info.append([game_data, game_tup[1]])
    print(related_games_info)

    return render_template('search.html', results=related_games_info)

if __name__ == "__main__":
    dataset = Dataset()
    print("Flask app running at http://0.0.0.0:5000")
    socketio.run(app, host="0.0.0.0", port=5000)
