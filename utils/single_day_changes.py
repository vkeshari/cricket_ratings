import math

from datetime import date, timedelta, datetime
from os import listdir
from pathlib import Path
import numpy as np

ONE_DAY = timedelta(days = 1)

# ['batting', 'bowling', 'allrounder']
TYPE = 'batting'
# ['test', 'odi', 't20']
FORMAT = 't20'

# Graph date range
START_DATE = date(2009, 1, 1)
END_DATE = date(2024, 1, 1)
SKIP_YEARS = list(range(1913, 1921)) + list(range(1940, 1946)) + [2020]

# Upper and lower bounds of ratings to show
THRESHOLD = 500
MAX_RATING = 1000

# ['', 'rating', 'rank', 'either', 'both']
CHANGED_DAYS_CRITERIA = 'rating'

SHOW_TOP_CHANGES = True
NUM_SHOW = 20

SHOW_GRAPH = True
BIN_WIDTH = 10
MAX_CHANGE = 250

# Alternate way to calculate allrounder ratings. Use geometric mean of batting and bowling.
ALLROUNDERS_GEOM_MEAN = True

assert TYPE in ['batting', 'bowling', 'allrounder'], "Invalid TYPE provided"
assert FORMAT in ['test', 'odi', 't20'], "Invalid FORMAT provided"
assert START_DATE < END_DATE, "START_DATE must be earlier than END_DATE"
assert END_DATE <= date.today(), "Future END_DATE requested"

assert MAX_RATING <= 1000, "MAX_RATING must not be greater than 1000"
assert THRESHOLD >= 0 and THRESHOLD < MAX_RATING, \
      "THRESHOLD must be between 0 and MAX_RATING"

assert CHANGED_DAYS_CRITERIA in ['', 'rating', 'rank', 'either', 'both']

assert NUM_SHOW >= 5, "NUM_SHOW should be at least 5"
assert BIN_WIDTH >= 5 and BIN_WIDTH <= 100, "BIN_WIDTH must be between 5 and 100"
assert MAX_CHANGE >= 100 and MAX_CHANGE <= 500, "MAX_CHANGE must be between 100 and 500"
assert MAX_CHANGE % BIN_WIDTH == 0, "MAX_CHANGE must be a multiple of BIN_WIDTH"

print (FORMAT + '\t' + TYPE)
print (str(START_DATE) + ' to ' + str(END_DATE))
print (str(THRESHOLD) + ' : ' + str(MAX_RATING))

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

daily_ratings, _ = get_daily_ratings()
print("Daily ratings data built for " + str(len(daily_ratings)) + " days" )

first_date = min(daily_ratings.keys())
last_date = max(daily_ratings.keys())


all_changes = []
last_player_ratings = {}
for d in daily_ratings:
  for p in daily_ratings[d]:
    if p not in last_player_ratings:
      last_player_ratings[p] = 0
    if last_player_ratings[p] > 0:
      rating = daily_ratings[d][p]
      last_rating = last_player_ratings[p]
      if rating >= THRESHOLD or last_rating >= THRESHOLD:
        change = rating - last_rating
        if not change == 0:
          all_changes.append((change, rating, d, p))
    last_player_ratings[p] = daily_ratings[d][p]

all_changes = sorted(all_changes, key = lambda c: c[0], reverse = True)

top_increases = all_changes[ : NUM_SHOW]
top_decreases = reversed(all_changes[-NUM_SHOW : ])


def readable_name(p):
  sep = p.find('_')
  return p[sep + 1 : ].split('.')[0].replace('_', ' ')

def country(p):
  return p.split('_')[0]

def full_readable_name(p):
  return readable_name(p) + ' (' + country(p) + ')'

if SHOW_TOP_CHANGES:
  print()
  print("Top daily rating gains")
  print("Gain\tRating\tDate\tPlayer")
  for c, r, d, p in top_increases:
    print('{c:3d}\t{r:3d}\t{d}\t{p}'.format(c = c, r = r, d = str(d), \
                                            p = full_readable_name(p)))
  print()
  print("Top daily rating drops")
  print("Drop\tRating\tDate\tPlayer")
  for c, r, d, p in top_decreases:
    print('{c:3d}\t{r:3d}\t{d}\t{p}'.format(c = c, r = r, d = str(d), \
                                            p = full_readable_name(p)))


from matplotlib import pyplot as plt

if SHOW_GRAPH:
  resolution = tuple([7.2, 7.2])

  fig, ax = plt.subplots(figsize = resolution)

  changes = [c[0] for c in all_changes]
  change_bins = list(range(-MAX_CHANGE, MAX_CHANGE + 1, BIN_WIDTH))

  title = 'Distribution of daily rating changes: ' + FORMAT + ' ' + TYPE \
          + '\n' + str(START_DATE) + ' to ' + str(END_DATE)

  ax.set_title(title, fontsize ='xx-large')

  ax.set_xlabel('Daily Rating Change', fontsize ='x-large')
  ax.set_ylabel('No. of changes', fontsize ='x-large')

  ax.set_xlim(-MAX_CHANGE, MAX_CHANGE)
  xticks = [x for x in change_bins if x % 50 == 0]
  ax.set_xticks(xticks)
  ax.set_xticklabels([str(x) for x in xticks], fontsize ='large')

  plt.yscale('log')
  ax.set_ylim(1, math.pow(10, 5))
  yticks = []
  for p in range(0, 5):
    yticks.append(int(math.pow(10, p)))
  ax.set_yticks(yticks)
  ax.set_yticklabels([str(y) for y in yticks], fontsize ='large')

  ax.grid(True, which = 'both', axis = 'both', alpha = 0.5)

  ax.hist(changes, bins = change_bins, \
            cumulative = False, align = 'mid', color = 'blue', alpha = 0.5)

  fig.tight_layout()
  plt.show()
