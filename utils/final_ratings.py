from datetime import date, datetime
from os import listdir

# ['batting', 'bowling', 'allrounder']
TYPE = ''
# ['test', 'odi', 't20']
FORMAT = ''
PLAYERS_DIR = 'players/' + TYPE + '/' + FORMAT

MAX_PLAYERS = 25

EPOCH = date(year = 1901, month = 1, day = 1)

assert TYPE in ['batting', 'bowling', 'allrounder'], "Invalid TYPE provided"
assert FORMAT in ['test', 'odi', 't20'], "Invalid FORMAT provided"
assert MAX_PLAYERS > 0, "MAX_PLAYERS must be positive"

def string_to_date(s):
  dt = datetime.strptime(s, '%Y%m%d')
  return date(dt.year, dt.month, dt.day)

def date_to_string(d):
  yr = str(d.year)
  mn = str(d.month)
  if (d.month < 10):
    mn = '0' + mn
  dy = str(d.day)
  if (d.day < 10):
    dy = '0' + dy
  return yr + '-' + mn + '-' + dy

def readable_name(p):
  sep = p.find('_')
  return p[sep+1:].split('.')[0].replace('_', ' ')

def country(p):
  return p.split('_')[0]

def readable_name_and_country(p):
  return readable_name(p) + ' (' + country(p) + ')'

def get_last_ratings(players_dir):
  final_ratings = {}
  player_files = listdir(players_dir)

  max_d = EPOCH
  for p in player_files:
    lines = []
    with open(players_dir + '/' + p, 'r') as f:
      lines += f.readlines()

    min_rank = 100
    max_rating = 0
    for l in lines:
      parts = l.split(',')
      d = string_to_date(parts[0])
      if d > max_d:
        max_d = d

      rating = eval(parts[2])
      if rating > max_rating:
        max_rating = rating

      rank = eval(parts[1])
      if rank < min_rank:
        min_rank = rank

    final_ratings[p] = {'last_date': d, 'rank': rank, 'final': rating, \
                        'max_rating': max_rating, 'min_rank': min_rank}

  actual_final_ratings = {k: v for (k, v) in final_ratings.items()
                          if v['last_date'] < max_d}

  return actual_final_ratings

final_ratings = get_last_ratings(PLAYERS_DIR)

sorted_final_ratings = dict(sorted(final_ratings.items(),
                                    key = lambda item: item[1]['final'],
                                    reverse = True))

print ("Players by final career rating at retirement:" + '\t' + FORMAT + '\t' + TYPE)
for i, p in enumerate(sorted_final_ratings)[ : MAX_PLAYERS]:
  final_rank = sorted_final_ratings[p]['rank']
  final_rating = sorted_final_ratings[p]['final']
  max_rating = sorted_final_ratings[p]['max_rating']
  min_rank = sorted_final_ratings[p]['min_rank']
  last_date = sorted_final_ratings[p]['last_date']
  print (str(i + 1) + '\tRetired: ' + date_to_string(last_date)
          + '\tFinal Rank: ' + str(final_rank) + '\tFinal Rating: ' + str(final_rating) \
          + '\t' + readable_name_and_country(p))
