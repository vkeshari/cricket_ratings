from datetime import date, datetime
from os import listdir

# ['batting', 'bowling', 'allrounder']
TYPE = 'batting'
# ['test', 'odi', 't20']
FORMAT = 't20'
PLAYERS_DIR = 'players/' + TYPE + '/' + FORMAT

START_DATE = date(2021, 1, 1)
END_DATE = date(2024, 1, 1)

MAX_RATING = 1000
THRESHOLD = 700

COMPARE_RANKS = [1, 2, 3]
COMPARE_PLAYERS = []

# ['', 'rating', 'rank', 'either', 'both']
CHANGED_DAYS_CRITERIA = 'either'

# Alternate way to calculate allrounder ratings. Use geometric mean of batting and bowling.
ALLROUNDERS_GEOM_MEAN = True

assert TYPE in ['batting', 'bowling', 'allrounder'], "Invalid TYPE provided"
assert FORMAT in ['test', 'odi', 't20'], "Invalid FORMAT provided"
assert START_DATE < END_DATE, "START_DATE must be earlier than END_DATE"
assert END_DATE <= date.today(), "Future END_DATE requested"

assert MAX_RATING <= 1000, "MAX_RATING must not be greater than 1000"
assert THRESHOLD >= 0 and THRESHOLD < MAX_RATING, \
      "THRESHOLD must be between 0 and MAX_RATING"

for r in COMPARE_RANKS:
  assert r > 0 and r <= 10, "Each rank in COMPARE_RANKS must be between 1 and 10"
if COMPARE_RANKS:
  assert not COMPARE_PLAYERS, "Both COMPARE_RANKS and COMPARE_PLAYERS cannot be set"
if COMPARE_PLAYERS:
  assert not COMPARE_RANKS, "Both COMPARE_RANKS and COMPARE_PLAYERS cannot be set"

assert CHANGED_DAYS_CRITERIA in ['', 'rating', 'rank', 'either', 'both']

print (FORMAT + ' : ' + TYPE)
print (str(START_DATE) + ' : ' + str(END_DATE))

for i, p in enumerate(COMPARE_PLAYERS):
  COMPARE_PLAYERS[i] = p + '.data'

def string_to_date(s):
  dt = datetime.strptime(s, '%Y%m%d')
  return date(dt.year, dt.month, dt.day)

def get_days_with_change(daily_data):
  changed_days = set()
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
      changed_days.add(d)
    last_daily_data = daily_data[d]

  return changed_days

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

  if CHANGED_DAYS_CRITERIA:
    rating_change_days = set()
    rank_change_days = set()
    if CHANGED_DAYS_CRITERIA in {'rating', 'either', 'both'}:
      rating_change_days = get_days_with_change(daily_ratings)
    if CHANGED_DAYS_CRITERIA in {'rank', 'either', 'both'}:
      rank_change_days = get_days_with_change(daily_ranks)

    change_days = set()
    if CHANGED_DAYS_CRITERIA in {'rating', 'rank', 'either'}:
      change_days = rating_change_days | rank_change_days
    elif CHANGED_DAYS_CRITERIA == 'both':
      change_days = rating_change_days & rank_change_days

    daily_ratings = dict(filter(lambda item: item[0] in change_days, \
                              daily_ratings.items()))
    daily_ranks = dict(filter(lambda item: item[0] in change_days, \
                            daily_ranks.items()))

  return daily_ratings, daily_ranks

daily_ratings, daily_ranks = get_daily_ratings()
print("Daily ranks data built for " + str(len(daily_ratings)) + " days" )


def get_compare_stats(daily_ratings, daily_ranks, \
                        compare_players, compare_ranks, start_date, end_date):
  if compare_players and compare_ranks:
    print ("Both players and ranks list provided")
    return {}
  if not daily_ratings or not daily_ranks:
    print ("Daily ratings or rankings are empty")
    return {}
  if not daily_ratings.keys() == daily_ranks.keys():
    print ("Key mismatch between daily ratings and ranks")
    return {}

  invalid_players = compare_players
  for d in daily_ratings:
    invalid_players = invalid_players - daily_ratings[d].keys()
    if not invalid_players:
      break
  if invalid_players:
    print("Invalid player name(s)")
    print(invalid_players)
    return {}

  compare_stats = {}
  for d in daily_ratings:
    if d < start_date or d > end_date:
      continue

    for p in daily_ratings[d]:
      rating = daily_ratings[d][p]
      rank = daily_ranks[d][p]

      if p in compare_players:
        if p not in compare_stats:
          compare_stats[p] = {}
        compare_stats[p][d] = rating
      elif rank in compare_ranks:
        if rank not in compare_stats:
          compare_stats[rank] = {}
        compare_stats[rank][d] = rating

  return compare_stats

compare_stats = get_compare_stats(daily_ratings, daily_ranks, \
                                  COMPARE_PLAYERS, COMPARE_RANKS, START_DATE, END_DATE)
print("Compare stats built with " + str(len(compare_stats)) + " keys")

def readable_name(p):
  sep = p.find('_')
  return p[sep + 1 : ].split('.')[0].replace('_', ' ')

def country(p):
  return p.split('_')[0]

def readable_name_and_country(p):
  return readable_name(p) + ' (' + country(p) + ')'

from matplotlib import pyplot as plt, cm
import numpy as np

colorscale = cm.tab20
resolution = tuple([7.2, 7.2])
fig, ax = plt.subplots(figsize = resolution)

ax.set_title("Comparison of " + FORMAT + ' ' + TYPE + ' ' + "players" \
                  + "\n" + str(START_DATE) + " to " + str(END_DATE), \
              fontsize ='xx-large')

if COMPARE_PLAYERS:
  color_stops = np.linspace(0, 1, len(COMPARE_PLAYERS) + 1)
  colors = colorscale(color_stops)
  ax.grid(True, which = 'both', axis = 'x', alpha = 0.5)

  for i, p in enumerate(COMPARE_PLAYERS):
    (xs, ys) = [], []
    if p in compare_stats:
      (xs, ys) = zip(*compare_stats[p].items())

    plt.plot(xs, ys, linestyle = '-', linewidth = 5, antialiased = True, \
                      alpha = 0.5, color = colors[i], label = readable_name_and_country(p))

elif COMPARE_RANKS:
  color_stops = np.linspace(0, 1, len(COMPARE_RANKS) + 1)
  colors = colorscale(color_stops)

  for i, rank in enumerate(COMPARE_RANKS):
    (xs, ys) = [], []
    if rank in compare_stats:
      (xs, ys) = zip(*compare_stats[rank].items())

    plt.plot(xs, ys, linestyle = '-', linewidth = 5, antialiased = True, \
                      alpha = 0.5, color = colors[i], label = 'Rank ' + str(rank))

ax.set_ylim(THRESHOLD, MAX_RATING)
ax.set_xlim(START_DATE, END_DATE)
ax.legend(loc = 'best', fontsize = 'medium')
ax.grid(True, which = 'both', axis = 'both', alpha = 0.5)

fig.tight_layout()
plt.show()
