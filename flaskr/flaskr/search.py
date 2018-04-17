import csv
import copy
import operator
import sys
import os

class Game(object):
    """
        Game class
    """

    def __init__(self, name, bgg_url, min_players, max_players, avg_time, min_time, max_time, avg_rating,
        geek_rating, num_votes, image_url, age, mechanic, owned, category, complexity, rank):

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

class Dataset(object):
    """
        This class is an abstract representation of our dataset
    """

    def __init__(self):

        # All the info on the games in one place
        self.games = dict()

        # Get absolute path
        script_dir = os.path.dirname(__file__) 
        rel_path = "data/2018_01.csv"
        abs_file_path = os.path.join(script_dir, rel_path)

        # Open csv, iterate through data
        with open(abs_file_path, 'rb') as f:
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

                self.games[name] = Game(name, url, min_players, max_players, avg_time, min_time,
                    max_time, rating, g_rating, votes, image, age, mechanic, owned, categories, complexity, rank)

        print self.games.get("Catan")

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
        if name == vector.name:
            continue

        # If categories shared award points
        if vector.categories != None:
            common = set(info.categories).intersection(vector.categories)
            if len(common) > 0:
                scores[name] += 2
            if len(common) > 1:
                scores[name] += 2
            if len(common) > 2:
                scores[name] += 2
            if len(common) > 3:
                scores[name] += 2
            if len(common) > 4:
                scores[name] += 2
            if len(common) > 5:
                scores[name] += 2

        # If mechanic shared award points
        if vector.mechanic != None:
            common = set(info.mechanic).intersection(vector.mechanic)
            if len(common) > 0:
                scores[name] += 2
            if len(common) > 1:
                scores[name] += 2
            if len(common) > 2:
                scores[name] += 2
            if len(common) > 3:
                scores[name] += 2
            if len(common) > 4:
                scores[name] += 2
            if len(common) > 5:
                scores[name] += 2

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
            scores[name] += 2
        if info.owned > 9000:
            scores[name] += 2

        # Remove weight from games that are not common
        # Remove more if significantly less common
        if info.owned < 2700:
            scores[name] -= 2
        if info.owned < 500:
            scores[name] -= 2

        # Add weight for games w more than average votes
        # Add more if significantly highly voted
        if info.num_votes >= 1773:
            scores[name] += 2
        if info.num_votes > 6000:
            scores[name] += 2
        if info.num_votes > 10000:
            scores[name] += 2

        # Lower weight for votes less than average
        # Lower even more if it has very few
        if info.num_votes < 1773:
            scores[name] -= 2
        if info.num_votes < 500:
            scores[name] -= 2

        # Add points if in top 50%, 25%, 10%, 5%
        if info.rank < (.5 * 5329):
            scores[name] += 4
        if info.rank < (.25 * 5329):
            scores[name] += 4
        if info.rank < (.1 * 5329):
            scores[name] += 4
        if info.rank < (.05 * 5329):
            scores[name] += 4

        # Lower weight for low rated games, bottom 50%, 25%, 10%, 5%
        if info.rank > (.5 * 5329):
            scores[name] -= 4
        if info.rank > (.25 * 5329):
            scores[name] -= 4
        if info.rank > (.1 * 5329):
            scores[name] -= 4
        if info.rank > (.05 * 5329):
            scores[name] -= 4

    sorted_scores = sorted(scores.items(), key=operator.itemgetter(1), reverse=True)
    return sorted_scores

def getRelatedGames(dataset, name):
    """
        Takes in a name of a game and returns an array of 10 games similar to that game.
    """
    if dataset.exists(name):
        results = score(dataset, dataset.games[name])
        print(results[0:10])
        return results
    else:
        print "Could not locate game"
        return []

def doAdvancedSearch(dataset, n_players, age, length, complexity, genres):
    """
        Does an advanced search based on parameters given.
    """
    min_players = n_players-2
    max_players = n_players+2
    min_time = length - 30
    max_time = length + 30
    new_game = Game(None, None, min_players, max_players, length, min_time,
            max_time, None, None, None, None, age, None, None, genres, complexity, None)
    results = score(dataset, new_game)
    print(results[0:10])
    return new_game, results

if __name__ == "__main__":
    args = sys.argv
    d = Dataset()
    if args[1] == '0':
        getRelatedGames(d, 'Catan')
    else:
        doAdvancedSearch(d, 4, 14, 120, 3, ["strategy","Co-operative Play"])

