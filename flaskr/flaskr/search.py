import csv
import copy
import operator
import sys
import os
import numpy as np
import scipy
from numpy.linalg import svd
from scipy.sparse.linalg import svds
import time
import pandas as pd
import cPickle as pickle

class Game(object):
    """
        Game class
    """

    def __init__(self, name, bgg_url, min_players, max_players, avg_time, min_time, max_time, avg_rating,
        geek_rating, num_votes, image_url, age, mechanic, owned, category, complexity, rank, vector, V):

        self.name = name
        self.url = bgg_url
        self.min_players = min_players
        self.max_players = max_players
        self.avg_time = avg_time
        self.min_time = min_time
        self.max_time = max_time
        self.avg_rating = avg_rating
        self.geek_rating = geek_rating
        self.num_votes = num_votes
        self.image = image_url
        self.age = age
        self.mechanic = mechanic
        self.owned = owned
        self.categories = category
        self.complexity = complexity
        self.rank = rank
        self.tf_idf_vector = vector
        self.svd = V

class Dataset(object):
    """
        This class is an abstract representation of our dataset
    """

    def __init__(self):

        # All the info on the games in one place
        self.games = dict()

        # Get absolute paths
        script_dir = os.path.dirname(__file__)
        rel_path = "data/2018_01.csv"
        data_file = os.path.join(script_dir, rel_path)
        rel_path = "data/tfidf.csv"
        tfidf_file = os.path.join(script_dir, rel_path)
        rel_path = "data/u.npy"
        u_file = os.path.join(script_dir, rel_path)
        rel_path = "data/v.npy"
        v_file = os.path.join(script_dir, rel_path)
        rel_path = "data/e.npy"
        e_file = os.path.join(script_dir, rel_path)
        rel_path = "data/tfidf.npz"
        tfidf_np_file = os.path.join(script_dir, rel_path)
        rel_path = "data/game_map.csv"
        map_file = os.path.join(script_dir, rel_path)

        # Pull in game map
        reader = csv.reader(open(map_file, 'r'))
        game_map = {}
        
        for k,v in reader:
            try:
                game_map[int(k)] = v
            except:
                continue

        # Open csv, iterate through data
        with open(data_file, 'rb') as f:
            reader = csv.DictReader(f)
            for row in reader:

                # Get the name, drop it if we already have it
                name = str(row['names']).upper()

                if self.games.get(name) != None:
                    continue

                # Get all the stuff we need, add it to global dict
                url = row['bgg_url']
                age = int(row['age'])
                image = row['image_url']
                rating = row['avg_rating']
                g_rating = row['geek_rating']
                min_players = row['min_players']
                max_players = row['max_players']
                avg_time = int(row['avg_time'])
                min_time = row['min_time']
                max_time = row['max_time']
                owned = row['owned']
                votes = row['num_votes']
                categories = row['category'].strip(' ').split(',')
                mechanic = row['mechanic'].split(',')
                complexity = float(row['weight'])
                rank = int(row['rank'])
                current_tf_idf = None
                svd_row = None

                self.games[name] = Game(name, url, min_players, max_players, avg_time, min_time,
                max_time, rating, g_rating, votes, image, age, mechanic, owned, categories, complexity, rank, current_tf_idf, svd_row)

            f.close()

        #original tf-idf stuff
        # result = np.array(list(csv.reader(open('data/tfidf.csv', "rb"), delimiter=",")))
        # result1 = np.delete(result,0,0) ##delete first row

        # #use these lines to get the game map
        # df = pd.DataFrame.from_dict(game_map, orient="index")
        # df.to_csv("data/game_map.csv")

        # ##creating the tfidf.npz
        # print 'result1'
        # result2 = np.delete(result1,0,1) ## delete first column
        # print 'result2'
        # insertion = np.arange(0,4999)
        # result3 = np.insert(result2,0,insertion,axis=1)
        # result3 = result3.astype('float')
        # print 'result3'
        # split = np.array_split(result3,500)
        # print len(split)

        save1 = time.time()
        # np.savez_compressed('data/mat.npz', *split)
        container = np.load(script_dir + '/data/mat.npz')
        save2 = time.time()
        print save2 - save1, 'np savez time'
 
        load1 = time.time()
        for arr in container.keys(): #'arr_0'
            for row in container[arr]: #rows in array
                self.games[game_map[int(row[0])]].tf_idf_vector = row[1:]
        load2 = time.time()
        print 'tf idfs loaded', load2 - load1

    def exists(self, name):
        """
            Checks to see if game name exists in the dataset
        """
        if self.games.get(name) == None:
            return False
        return True

    def getGames(self):
        return self.games

def score(dataset, vector):
    """
        Scoring function for the dataset
        Takes in vector of characteristics
    """

    all_games = copy.copy(dataset.getGames())
    scores = dict()

    for name, info in all_games.items():

        # Start at 0
        scores[name] = 0

        # Ignore same game
        if (name == vector.name) or (name in vector.name):
            continue

        # Only do this if we have a vector
        try:
            if vector.tf_idf_vector == None:
                pass
        except:
            if vector.tf_idf_vector.any() != None:
                scores[name] += (np.dot(vector.tf_idf_vector, np.array(info.tf_idf_vector, dtype=float)) /
                     np.dot(vector.tf_idf_vector, vector.tf_idf_vector)) * 20

        # If categories shared award points
        if vector.categories != None:
            common = set(info.categories).intersection(vector.categories)
            if len(common) > 0:
                scores[name] += 1
            if len(common) > 1:
                scores[name] += 1
            if len(common) > 2:
                scores[name] += 1
            if len(common) > 3:
                scores[name] += 1
            if len(common) > 4:
                scores[name] += 1
            if len(common) > 5:
                scores[name] += 1

        # If mechanic shared award points
        if vector.mechanic != None:
            common = set(info.mechanic).intersection(vector.mechanic)
            if len(common) > 0:
                scores[name] += 1
            if len(common) > 1:
                scores[name] += 1
            if len(common) > 2:
                scores[name] += 1
            if len(common) > 3:
                scores[name] += 1
            if len(common) > 4:
                scores[name] += 1
            if len(common) > 5:
                scores[name] += 1

        # If the complexity is within a certain range award points. If they're closer together
        # award more points
        if (info.complexity <= vector.complexity + 1) and (info.complexity >= vector.complexity - 1):
            scores[name] += 2
        if (info.complexity <= vector.complexity + .8) and (info.complexity >= vector.complexity - .8):
            scores[name] += 2
        if (info.complexity <= vector.complexity + .5) and (info.complexity >= vector.complexity - .5):
            scores[name] += 2
        if (info.complexity <= vector.complexity + .3) and (info.complexity >= vector.complexity - .3):
            scores[name] += 2
        if (info.complexity <= vector.complexity + .1) and (info.complexity >= vector.complexity - .1):
            scores[name] += 2


        # Average time is within a certain range, awared points
        if (info.avg_time + 90 < vector.avg_time) and (info.avg_time - 90 > vector.avg_time):
            scores[name] += 2
        if (info.avg_time + 60 < vector.avg_time) and (info.avg_time - 60 > vector.avg_time):
            scores[name] += 2
        if (info.avg_time + 30 < vector.avg_time) and (info.avg_time - 30 > vector.avg_time):
            scores[name] += 2

        # Lower weight for lower than average rated games
        if info.avg_rating < 7:
            scores[name] -= 3
        if info.avg_time < 6:
            scores[name] -= 3

        # Add weight to games that are owned by more than average
        # Add more if 1 std above average
        if info.owned >= 2700:
            scores[name] += 5
        if info.owned > 9000:
            scores[name] += 5

        # Remove weight from games that are not common
        # Remove more if significantly less common
        if info.owned < 2700:
            scores[name] -= 2
        if info.owned < 500:
            scores[name] -= 2

        # Add weight for games w more than average votes
        # Add more if significantly highly voted
        if info.num_votes >= 1773:
            scores[name] += 4
        if info.num_votes > 6000:
            scores[name] += 4
        if info.num_votes > 10000:
            scores[name] += 4

        # Lower weight for votes less than average
        # Lower even more if it has very few
        if info.num_votes < 1773:
            scores[name] -= 2
        if info.num_votes < 500:
            scores[name] -= 2

        # Add points if in top 50%, 25%, 10%, 5%
        if info.rank < (.5 * 5329):
            scores[name] += 2
        if info.rank < (.25 * 5329):
            scores[name] += 2
        if info.rank < (.1 * 5329):
            scores[name] += 2
        if info.rank < (.05 * 5329):
            scores[name] += 2

        # Lower weight for low rated games, bottom 50%, 25%, 10%, 5%
        if info.rank > (.5 * 5329):
            scores[name] -= 2
        if info.rank > (.25 * 5329):
            scores[name] -= 2
        if info.rank > (.1 * 5329):
            scores[name] -= 2
        if info.rank > (.05 * 5329):
            scores[name] -= 2

    sorted_scores = sorted(scores.items(), key=operator.itemgetter(1), reverse=True)
    return sorted_scores

def getRelatedMultipleGames(dataset, games):
    """
        Takes in a list of games and finds games related to those games
    """

    min_players = 100
    max_players = 0
    min_time = 10000
    max_time = 0
    length = (0, 0)
    age = (0, 0)
    mechanics = set()
    genres = set()
    complexity = (0, 0)

    for g in games:

        game = dataset.getGames()[g]

        # Bound min/max players on lowest/highest values
        if game.min_players < min_players:
            min_players = game.min_players
        if game.max_players > max_players:
            max_players = game.max_players

        # Bound min/max time on lowest/highest values
        if game.min_time < min_time:
            min_time = game.min_time
        if game.max_time > max_time:
            max_time = game.max_time

        # Handle length
        if length == 0:
            length = (game.avg_time, 1)
        else:
            length = ((length[0] + game.avg_time) / (length[1] + 1), length[1] + 1)

        # Handle age
        if age == 0:
            age = (game.age, 1)
        else:
            age = ((age[0] + game.age) / (age[1] + 1), age[1] + 1)

        # Handle complexity
        if complexity == 0:
            complexity = (game.complexity, 1)
        else:
            complexity = ((complexity[0] + game.complexity) / (complexity[1] + 1), complexity[1] + 1)

        # Handle mechanics, genres
        mechanics = set(mechanics.union(game.mechanic))
        genres = set(genres.union(game.categories))

    new_game = Game(games, None, min_players, max_players, length, min_time,
            max_time, None, None, None, None, age, mechanics, None, genres, complexity[0], None, None, None)
    results = score(dataset, new_game)
    print(results[0:10])
    return new_game, results

def getRelatedGames(dataset, name):
    """
        Takes in a name of a game and returns an array of 10 games similar to that game.
    """
    if dataset.exists(name):
        results = score(dataset, dataset.games[name])
        print(results[0:10])
        return results
    else:
        print("Could not locate game")
        return []

def doAdvancedSearch(dataset, n_players, age, length, complexity, mechanics, genres):
    """
        Does an advanced search based on parameters given.
    """
    min_players = n_players[0]
    max_players = n_players[1]
    min_time = 30*length;
    max_time = 30*length+30;
    if (length == 3):
        max_time = 1000;
    new_game = Game([], None, min_players, max_players, length*30, min_time, max_time, None,
        None, None, None, age, mechanics, None, genres, complexity[0], None, None, None)

    results = score(dataset, new_game)
    print(results[0:10])
    return new_game, results

if __name__ == "__main__":
    args = sys.argv
    d = Dataset()
    if args[1] == '0':
        getRelatedGames(d, 'CATAN')
    else:
        # doAdvancedSearch(d, 4, 14, 120, 3, ["strategy","Co-operative Play"])
        getRelatedMultipleGames(d, ['CATAN'])
