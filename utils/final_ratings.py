from common.output import string_to_date, date_to_string, readable_name_and_country

from datetime import date
from os import listdir

# ['batting', 'bowling', 'allrounder']
TYPE = 'batting'
# ['test', 'odi', 't20']
FORMAT = 't20'
PLAYERS_DIR = 'players/' + TYPE + '/' + FORMAT

MAX_PLAYERS = 25
BY_FINAL_RANK = False

EPOCH = date(year = 1901, month = 1, day = 1)

assert TYPE in ['batting', 'bowling', 'allrounder'], "Invalid TYPE provided"
assert FORMAT in ['test', 'odi', 't20'], "Invalid FORMAT provided"
assert MAX_PLAYERS > 0, "MAX_PLAYERS must be positive"

if BY_FINAL_RANK:
  assert not TYPE == 'allrounder', "BY_FINAL_RANK not supported for allrounders"

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

  # Remove players that haven't retired
  actual_final_ratings = {k: v for (k, v) in final_ratings.items()
                          if v['last_date'] < max_d}

  return actual_final_ratings

final_ratings = get_last_ratings(PLAYERS_DIR)


if BY_FINAL_RANK:
  sorted_final_ratings = dict(sorted(final_ratings.items(),
                                      key = lambda item: (-item[1]['rank'], \
                                                          item[1]['final']), \
                                      reverse = True))
else:
  sorted_final_ratings = dict(sorted(final_ratings.items(),
                                      key = lambda item: item[1]['final'],
                                      reverse = True))


print ("Players by final career rating at retirement:" + '\t' + FORMAT + '\t' + TYPE)
for i, p in enumerate(sorted_final_ratings):
  final_rank = sorted_final_ratings[p]['rank']
  final_rating = sorted_final_ratings[p]['final']
  max_rating = sorted_final_ratings[p]['max_rating']
  min_rank = sorted_final_ratings[p]['min_rank']
  last_date = sorted_final_ratings[p]['last_date']
  print (str(i + 1) + '\tRetired: ' + date_to_string(last_date)
          + '\tFinal Rank: ' + str(final_rank) + '\tFinal Rating: ' + str(final_rating) \
          + '\t' + readable_name_and_country(p))
  if i == MAX_PLAYERS - 1:
    break
