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

class Game(object):
    """
        Game class
    """

    def __init__(self, name, bgg_url, min_players, max_players, avg_time, min_time, max_time, avg_rating,
        geek_rating, num_votes, image_url, age, mechanic, owned, category, complexity, rank, vector, V, sent):

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
        self.sentiment = sent

class Dataset(object):
    """
        This class is an abstract representation of our dataset
    """

    def __init__(self):

        # All the info on the games in one place
        self.games = dict()

        # Get absolute paths
        script_dir = os.path.dirname(__file__)

        #all game data
        rel_path = "data/bgg_data_v3.csv"
        data_file = os.path.join(script_dir, rel_path)

        #tf idf original file (big)
        rel_path = "data/tfidf_v3.csv"
        tfidf_file = os.path.join(script_dir, rel_path)

        #svd numpy arrays
        rel_path = "data/svd.npz"
        tfidf_np_file = os.path.join(script_dir, rel_path)

        #dictionary for mapping indices to games
        rel_path = "data/game_names_v3.csv"
        map_file = os.path.join(script_dir, rel_path)

        #sentiments
        rel_path = "data/game_sentiments_v3.csv"
        sent_file = os.path.join(script_dir, rel_path)

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
                max_time, rating, g_rating, votes, image, age, mechanic, owned, categories, complexity,
                rank, current_tf_idf, svd_row, False)

            f.close()

        # Load the SVD game matrix and populate tf-idf vectors
        container = np.load(tfidf_np_file)['idx_U']
        for row in container:
            self.games[game_map[int(row[0])].upper()].tf_idf_vector = row[1:]

        # Do sentiment
        with open(sent_file, 'rb') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if self.games.get(row['names']) != None:
                    self.games.get(row['names']).sentiment = row['boolean']
                else:
                    continue

    def exists(self, name):
        """
            Checks to see if game name exists in the dataset
        """
        if self.games.get(name) == None:
            return False
        return True

    def getGames(self):
        return self.games

def score(dataset, vector, advanced):
    """
        Scoring function for the dataset
        Takes in vector of characteristics
    """

    all_games = copy.copy(dataset.getGames())
    scores = dict()

    for name, info in all_games.items():

        # Start at 0
        scores[name] = [0, []]

        # Ignore same game
        if (name == vector.name) or (name in vector.name):
            continue

        # Heavily weight games that are in the same player range
        if advanced:
            if int(info.max_players) >= int(vector.max_players):
                scores[name][0] += 10
            else:
                del scores[name]
                continue

        # Only do this if we have a vector
        try:
            if vector.tf_idf_vector == None:
                pass
        except:
            if vector.tf_idf_vector.any() != None:
                scores[name][0] += (np.dot(vector.tf_idf_vector, np.array(info.tf_idf_vector, dtype=float)) /
                    np.dot(vector.tf_idf_vector, vector.tf_idf_vector)) * 7

        # Add sentiment
        if info.sentiment == True:
            scores[name] += 10

        # If categories shared award points
        cat_score = 0
        if advanced:
            common = set(info.categories).intersection(vector.categories)
            #if a user entered in a category, they really want that
            if len(common) > 0:
                scores[name][0] += 10
                cat_score += 10
            if len(common) > 1:
                scores[name][0] += 10
                cat_score += 5
            if len(common) > 2:
                scores[name][0] += 5
                cat_score += 5
        else:
            if vector.categories != None:
                common = set(info.categories).intersection(vector.categories)
                if len(common) > 0:
                    scores[name][0] += 1
                    cat_score += 1
                if len(common) > 1:
                    scores[name][0] += 1
                    cat_score += 1
                if len(common) > 2:
                    scores[name][0] += 1
                    cat_score += 1
                if len(common) > 3:
                    scores[name][0] += 1
                    cat_score += 1
                if len(common) > 4:
                    scores[name][0] += 1
                    cat_score += 1
                if len(common) > 5:
                    scores[name][0] += 1
                    cat_score += 1

        # If mechanic shared award points
        mech_score = 0
        if advanced:
            #if a user entered in a mechanic, they really want that
            common = set(info.mechanic).intersection(vector.mechanic)
            if len(common) > 0:
                scores[name][0] += 10
                mech_score += 10
            if len(common) > 1:
                scores[name][0] += 10
                mech_score += 5
            if len(common) > 2:
                scores[name][0] += 5
                mech_score += 5
        else:
            if vector.mechanic != None:
                common = set(info.mechanic).intersection(vector.mechanic)
                if len(common) > 0:
                    scores[name][0] += 1
                    mech_score += 1
                if len(common) > 1:
                    scores[name][0] += 2
                    mech_score += 2
                if len(common) > 2:
                    scores[name][0] += 2
                    mech_score += 2
                if len(common) > 3:
                    scores[name][0] += 2
                    mech_score += 2
                if len(common) > 4:
                    scores[name][0] += 2
                    mech_score += 2
                if len(common) > 5:
                    scores[name][0] += 2
                    mech_score += 2

        # If the complexity is within a certain range award points. If they're closer together
        # award more points
        comp_score = 0

        if advanced:
            if (info.complexity >= vector.complexity[0]) and (info.complexity <= vector.complexity[1]):
                scores[name][0] += 10
                comp_score += 10
        else:
            if (info.complexity <= vector.complexity + 1) and (info.complexity >= vector.complexity - 1):
                scores[name][0] += 3
                comp_score += 3
            if (info.complexity <= vector.complexity + .8) and (info.complexity >= vector.complexity - .8):
                scores[name][0] += 3
                comp_score += 3
            if (info.complexity <= vector.complexity + .5) and (info.complexity >= vector.complexity - .5):
                scores[name][0] += 3
                comp_score += 3
            if (info.complexity <= vector.complexity + .3) and (info.complexity >= vector.complexity - .3):
                scores[name][0] += 3
                comp_score += 3
            if (info.complexity <= vector.complexity + .1) and (info.complexity >= vector.complexity - .1):
                scores[name][0] += 3
                comp_score += 3

        # Average time is within a certain range, awared points
        time_score = 0
        if advanced:
            #if your average time is within the bounds specificed
            if (info.avg_time >= vector.min_time) and (info.avg_time <= vector.max_time):
                scores[name][0] += 5
                time_score += 5
            #if your average time is within 15 minutes of average time specified
            if (info.avg_time <= vector.min_time + 15) and (info.avg_time >= vector.max_time - 15):
                scores[name][0] += 3
                time_score += 3
        else:
            #within 45 minute range of query's average time
            if (info.avg_time <= int(vector.min_time) + 45) and (info.avg_time >= int(vector.max_time) - 45):
                scores[name][0] += 3
                time_score += 3
            if (info.avg_time <= int(vector.min_time) + 30) and (info.avg_time >= int(vector.max_time) - 30):
                scores[name][0] += 3
                time_score += 3
            if (info.avg_time <= int(vector.min_time) + 15) and (info.avg_time >= int(vector.max_time) - 15):
                scores[name][0] += 3
                time_score += 3

        # Higher weight for higher than average rated games
        popularity_score = 0
        if info.avg_rating > 7:
            scores[name][0] += 5
            popularity_score += 5
        if info.avg_rating > 6:
            scores[name][0] += 5
            popularity_score += 5
        # Lower weight for lower than average rated games
        popularity_score = 0
        if info.avg_rating < 7:
            scores[name][0] -= 5
            popularity_score -= 5
        if info.avg_rating < 6:
            scores[name][0] -= 5
            popularity_score -= 5

        # Add weight to games that are owned by more than average
        # Add more if 1 std above average
        if info.owned >= 2700:
            scores[name][0] += 6
            popularity_score += 6
        if info.owned > 9000:
            scores[name][0] += 6
            popularity_score += 6

        # Remove weight from games that are not common
        # Remove more if significantly less common
        if info.owned < 2700:
            scores[name][0] -= 6
            popularity_score -= 6
        if info.owned < 500:
            scores[name][0] -= 6
            popularity_score -= 6

        # Add weight for games w more than average votes
        # Add more if significantly highly voted
        if info.num_votes >= 1773:
            scores[name][0] += 4
            popularity_score += 4
        if info.num_votes > 6000:
            scores[name][0] += 4
            popularity_score += 4
        if info.num_votes > 10000:
            scores[name][0] += 4
            popularity_score += 4

        # Lower weight for votes less than average
        # Lower even more if it has very few
        if info.num_votes < 1773:
            scores[name][0] -= 4
            popularity_score -= 4
        if info.num_votes < 500:
            scores[name][0] -= 4
            popularity_score -= 4

        # Add points if in top 50%, 25%, 10%, 5%
        if info.rank < (.5 * 5329):
            scores[name][0] += 2
            popularity_score += 2
        if info.rank < (.25 * 5329):
            scores[name][0] += 3
            popularity_score += 3
        if info.rank < (.1 * 5329):
            scores[name][0] += 4
            popularity_score += 4
        if info.rank < (.05 * 5329):
            scores[name][0] += 5
            popularity_score += 5

        # Lower weight for low rated games, bottom 50%, 25%, 10%, 5%
        if info.rank > 5239 - (.5 * 5329):
            scores[name][0] -= 2
            popularity_score -= 2
        if info.rank > 5239 - (.25 * 5329):
            scores[name][0] -= 3
            popularity_score -= 3
        if info.rank > 5239 - (.1 * 5329):
            scores[name][0] -= 4
            popularity_score -= 4
        if info.rank > 5239 - (.05 * 5329):
            scores[name][0] -= 5
            popularity_score -= 5

        if advanced:
            scores[name][1] = sorted({
                'Popularity' : popularity_score / 48,
                'Time' : time_score / 8,
                'Complexity' : comp_score / 10,
                'Mechanics' : mech_score / 20,
                'Categories' : cat_score / 20}, key=operator.itemgetter(1), reverse=True)
        else:
            scores[name][1] = sorted({
                'Popularity' : popularity_score / 30,
                'Time' : time_score / 6,
                'Complexity' : comp_score / 10,
                'Mechanics' : mech_score / 6,
                'Categories' : cat_score / 6}, key=operator.itemgetter(1), reverse=True)

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
            max_time, None, None, None, None, age, mechanics, None, genres, complexity[0], None, None, None, False)
    results = score(dataset, new_game, False)
    print(results[0:30])
    return new_game, results

def getRelatedGames(dataset, name):
    """
        Takes in a name of a game and returns an array of 10 games similar to that game.
    """
    if dataset.exists(name):
        results = score(dataset, dataset.games[name], False)
        return results
    else:
        print("Could not locate game")
        return []

def doAdvancedSearch(dataset, n_players, length, complexity, mechanics, genres):
    """
        Does an advanced search based on parameters given.
    """
    min_players = n_players[0]
    max_players = n_players[1]
    min_time = 30 * (length-1);
    max_time = 30 * (length-1) + 30;

    complexity_ranges = [(1, 1.5), (1.5, 2), (2, 2.5), (2.5, 3), (3, 3.5), (3.5, 4.3), (4.3, 5)]
    adjusted_min = complexity_ranges[complexity[0] - 1][0]
    adjusted_max = complexity_ranges[complexity[1] - 1][1]
    adjusted_complexity = [adjusted_min, adjusted_max]

    if (length == 4):
        max_time = 1000;
    new_game = Game([], None, min_players, max_players, (min_time + max_time) / 2, min_time, max_time, None,
        None, None, None, None, mechanics, None, genres, adjusted_complexity, None, None, None, False)

    results = score(dataset, new_game, True)
    return new_game, results

if __name__ == "__main__":
    args = sys.argv
    d = Dataset()
    if args[1] == '0':
        getRelatedGames(d, 'CATAN')
    else:
        # doAdvancedSearch(d, 4, 14, 120, 3, ["strategy","Co-operative Play"])
        getRelatedMultipleGames(d, ['CATAN', 'PANDEMIC'])
