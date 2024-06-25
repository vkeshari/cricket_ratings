from datetime import date, datetime
from os import listdir

# ['batting', 'bowling', 'allrounder']
TYPE = ''
# ['test', 'odi', 't20']
FORMAT = ''
PLAYERS_DIR = 'players/' + TYPE + '/' + FORMAT

MAX_PLAYERS = 25
NUM_TOP = 10

assert TYPE in ['batting', 'bowling', 'allrounder'], "Invalid TYPE provided"
assert FORMAT in ['test', 'odi', 't20'], "Invalid FORMAT provided"
assert MAX_PLAYERS > 0, "MAX_PLAYERS must be positive"
assert NUM_TOP > 0, "NUM_TOP must be positive"

def readable_name(p):
  sep = p.find('_')
  return p[sep+1:].split('.')[0].replace('_', ' ')

def country(p):
  return p.split('_')[0]

def readable_name_and_country(p):
  return readable_name(p) + ' (' + country(p) + ')'

def get_top_ratings(players_dir, num_top):
  top_ratings = {}
  player_files = listdir(players_dir)

  for p in player_files:
    lines = []
    with open(players_dir + '/' + p, 'r') as f:
      lines += f.readlines()

    min_rank = 100
    max_rating = 0
    days_at_top = 0
    for l in lines:
      parts = l.split(',')

      rating = eval(parts[2])
      if rating > max_rating:
        max_rating = rating

      rank = eval(parts[1])
      if rank < min_rank:
        min_rank = rank
      if rank <= num_top:
        days_at_top += 1

    top_ratings[p] = {'days_at_top': days_at_top, 'min_rank': min_rank, 'max_rating': max_rating}

  return top_ratings

top_ratings = get_top_ratings(PLAYERS_DIR, NUM_TOP)

sorted_top_ratings = dict(sorted(top_ratings.items(),
                                    key = lambda item: item[1]['days_at_top'],
                                    reverse = True))

print ("Players by longest time spent at top " + str(NUM_TOP) + ' rankings :' \
        + '\t' + FORMAT + '\t' + TYPE)

for i, p in enumerate(sorted_top_ratings):
  days_at_top = sorted_top_ratings[p]['days_at_top']
  min_rank = sorted_top_ratings[p]['min_rank']
  max_rating = sorted_top_ratings[p]['max_rating']
  print (str(i + 1) + '\tMax Rating: ' + str(max_rating) + '\t\tBest Rank: ' \
          + str(min_rank) + '\tDays in top ' + str(NUM_TOP) + ': ' + str(days_at_top) \
          + '\t' + readable_name_and_country(p))

  if i > MAX_PLAYERS - 2:
    break
