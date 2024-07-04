from datetime import date, datetime
from os import listdir

# ['batting', 'bowling', 'allrounder']
TYPE = 'batting'
# ['test', 'odi', 't20']
FORMAT = 't20'
PLAYERS_DIR = 'players/' + TYPE + '/' + FORMAT

MAX_PLAYERS = 25
NUM_TOP = 1

CHANGED_DAYS_ONLY = False

# Alternate way to calculate allrounder ratings. Use geometric mean of batting and bowling.
ALLROUNDERS_GEOM_MEAN = True

assert TYPE in ['batting', 'bowling', 'allrounder'], "Invalid TYPE provided"
assert FORMAT in ['test', 'odi', 't20'], "Invalid FORMAT provided"
assert MAX_PLAYERS > 0, "MAX_PLAYERS must be positive"
assert NUM_TOP > 0, "NUM_TOP must be positive"

def string_to_date(s):
  dt = datetime.strptime(s, '%Y%m%d')
  return date(dt.year, dt.month, dt.day)

def get_changed_data(daily_data):
  changed_daily_data = {}
  last_daily_data = {}
  for d in daily_data:
    changed = False
    if not last_daily_data:
      changed = True
    elif not sorted(daily_data[d].keys()) == sorted(last_daily_data.keys()):
      changed = True
    else:
      for p in daily_data[d]:
        if not daily_data[d][p] == last_daily_data[p]:
          changed = True
          break
    if changed:
      changed_daily_data[d] = daily_data[d]
    last_daily_data = daily_data[d]

  return changed_daily_data

def get_daily_ratings():
  daily_ratings = {}
  daily_ranks = {}
  dates_parsed = set()

  player_files = listdir('players/' + TYPE + '/' + FORMAT)
  for p in player_files:
    lines = []
    with open('players/' + TYPE + '/' + FORMAT + '/' + p, 'r') as f:
      lines += f.readlines()

    for l in lines:
      parts = l.split(',')
      d = string_to_date(parts[0])
      if d not in dates_parsed:
        dates_parsed.add(d)
        daily_ratings[d] = {}
        daily_ranks[d] = {}

      rating = eval(parts[2])
      if TYPE == 'allrounder' and ALLROUNDERS_GEOM_MEAN:
        rating = int(math.sqrt(rating * 1000))
      daily_ratings[d][p] = rating

      rank = eval(parts[1])
      daily_ranks[d][p] = rank

  daily_ratings = dict(sorted(daily_ratings.items()))
  daily_ranks = dict(sorted(daily_ranks.items()))
  for d in dates_parsed:
    daily_ratings[d] = dict(sorted(daily_ratings[d].items(), \
                                    key = lambda item: item[1], reverse = True))
    daily_ranks[d] = dict(sorted(daily_ranks[d].items(), \
                                    key = lambda item: item[1]))

  if CHANGED_DAYS_ONLY:
    daily_ratings = get_changed_data(daily_ratings)
    daily_ranks = get_changed_data(daily_ranks)

  return daily_ratings, daily_ranks

daily_ratings, daily_ranks = get_daily_ratings()
print("Daily ranks data built for " + str(len(daily_ratings)) + " days" )


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

top_player_stats = get_top_player_stats(daily_ratings, daily_ranks, NUM_TOP)

sorted_top_stats = dict(sorted(top_player_stats.items(),
                                    key = lambda item: item[1]['days_at_top'],
                                    reverse = True))

def readable_name(p):
  sep = p.find('_')
  return p[sep + 1 : ].split('.')[0].replace('_', ' ')

def country(p):
  return p.split('_')[0]

def readable_name_and_country(p):
  return readable_name(p) + ' (' + country(p) + ')'

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
