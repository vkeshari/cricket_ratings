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

CHANGED_DAYS_ONLY = True

NUM_SHOW = 20

# Alternate way to calculate allrounder ratings. Use geometric mean of batting and bowling.
ALLROUNDERS_GEOM_MEAN = True

assert TYPE in ['batting', 'bowling', 'allrounder'], "Invalid TYPE provided"
assert FORMAT in ['test', 'odi', 't20'], "Invalid FORMAT provided"
assert START_DATE < END_DATE, "START_DATE must be earlier than END_DATE"
assert END_DATE <= date.today(), "Future END_DATE requested"

assert MAX_RATING <= 1000, "MAX_RATING must not be greater than 1000"
assert THRESHOLD >= 0 and THRESHOLD < MAX_RATING, \
      "THRESHOLD must be between 0 and MAX_RATING"

assert NUM_SHOW >= 5, "NUM_SHOW should be at least 5"

print (FORMAT + '\t' + TYPE)
print (str(START_DATE) + ' to ' + str(END_DATE))
print (str(THRESHOLD) + ' : ' + str(MAX_RATING))

def string_to_date(s):
  dt = datetime.strptime(s, '%Y%m%d')
  return date(dt.year, dt.month, dt.day)

def get_daily_ratings():
  daily_ratings = {}

  player_files = listdir('players/' + TYPE + '/' + FORMAT)
  for p in player_files:
    lines = []
    with open('players/' + TYPE + '/' + FORMAT + '/' + p, 'r') as f:
      lines += f.readlines()

    for l in lines:
      parts = l.split(',')
      d = string_to_date(parts[0])
      if d not in daily_ratings:
        daily_ratings[d] = {}

      rating = eval(parts[2])
      if TYPE == 'allrounder' and ALLROUNDERS_GEOM_MEAN:
        rating = int(math.sqrt(rating * 1000))
      daily_ratings[d][p] = rating

  daily_ratings = dict(sorted(daily_ratings.items()))
  for d in daily_ratings:
    daily_ratings[d] = dict(sorted(daily_ratings[d].items(), \
                                    key = lambda item: item[1], reverse = True))

  if CHANGED_DAYS_ONLY:
    changed_daily_ratings = {}
    last_daily_ratings = {}
    for d in daily_ratings:
      changed = False
      if not last_daily_ratings:
        changed = True
      elif not sorted(daily_ratings[d].keys()) == sorted(last_daily_ratings.keys()):
        changed = True
      else:
        for p in daily_ratings[d]:
          if not daily_ratings[d][p] == last_daily_ratings[p]:
            changed = True
            break
      if changed:
        changed_daily_ratings[d] = daily_ratings[d]
      last_daily_ratings = daily_ratings[d]
    daily_ratings = changed_daily_ratings

  return daily_ratings

daily_ratings = get_daily_ratings()
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
      if rating >= THRESHOLD or  last_rating >= THRESHOLD:
        change = rating - last_rating
        all_changes.append((change, rating, d, p))
    last_player_ratings[p] = daily_ratings[d][p]

all_changes = sorted(all_changes, key = lambda c: c[0], reverse = True)

top_increases = all_changes[ : NUM_SHOW]
top_decreases = reversed(all_changes[-NUM_SHOW : ])


def readable_name(p):
  sep = p.find('_')
  return p[sep+1:].split('.')[0].replace('_', ' ')

def country(p):
  return p.split('_')[0]

def full_readable_name(p):
  return readable_name(p) + ' (' + country(p) + ')'

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

