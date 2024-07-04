from common.data import get_daily_ratings
from common.output import string_to_date, readable_name_and_country

# ['batting', 'bowling', 'allrounder']
TYPE = 'batting'
# ['test', 'odi', 't20']
FORMAT = 't20'
PLAYERS_DIR = 'players/' + TYPE + '/' + FORMAT

MAX_PLAYERS = 25
NUM_TOP = 1

# ['', 'rating', 'rank', 'either', 'both']
CHANGED_DAYS_CRITERIA = 'either'

# Alternate way to calculate allrounder ratings. Use geometric mean of batting and bowling.
ALLROUNDERS_GEOM_MEAN = True

assert TYPE in ['batting', 'bowling', 'allrounder'], "Invalid TYPE provided"
assert FORMAT in ['test', 'odi', 't20'], "Invalid FORMAT provided"
assert MAX_PLAYERS > 0, "MAX_PLAYERS must be positive"
assert NUM_TOP > 0, "NUM_TOP must be positive"

assert CHANGED_DAYS_CRITERIA in ['', 'rating', 'rank', 'either', 'both']


def get_top_player_stats(daily_ratings, daily_ranks, num_top):
  player_stats = {}

  for d in daily_ranks:
    for p in daily_ranks[d]:
      if p not in player_stats:
        player_stats[p] = {'min_rank': 100, 'max_rating': 0, 'days_at_top': 0}

      rank = daily_ranks[d][p]
      if rank < player_stats[p]['min_rank']:
        player_stats[p]['min_rank'] = rank

      if rank <= num_top:
        player_stats[p]['days_at_top'] += 1

  for d in daily_ratings:
    for p in daily_ratings[d]:
      if p not in player_stats:
        player_stats[p] = {'min_rank': 100, 'max_rating': 0, 'days_at_top': 0}

      rating = daily_ratings[d][p]
      if rating > player_stats[p]['max_rating']:
        player_stats[p]['max_rating'] = rating

  return player_stats

daily_ratings, daily_ranks = get_daily_ratings(TYPE, FORMAT, \
                                  changed_days_criteria = CHANGED_DAYS_CRITERIA, \
                                  allrounders_geom_mean = ALLROUNDERS_GEOM_MEAN)

top_player_stats = get_top_player_stats(daily_ratings, daily_ranks, NUM_TOP)
sorted_top_stats = dict(sorted(top_player_stats.items(), \
                                    key = lambda item: (item[1]['days_at_top'], \
                                                        item[1]['min_rank'],
                                                        item[1]['max_rating']), \
                                    reverse = True))

print ("Players by longest time spent in top " + str(NUM_TOP) + ' rankings :' \
        + '\t' + FORMAT + '\t' + TYPE)

for i, p in enumerate(sorted_top_stats):
  days_at_top = sorted_top_stats[p]['days_at_top']
  min_rank = sorted_top_stats[p]['min_rank']
  max_rating = sorted_top_stats[p]['max_rating']
  print (str(i + 1) + '\tMax Rating: ' + str(max_rating) + '\t\tBest Rank: ' \
          + str(min_rank) + '\tDays in top ' + str(NUM_TOP) + ': ' + str(days_at_top) \
          + '\t' + readable_name_and_country(p))
  if i == MAX_PLAYERS - 1:
    break
