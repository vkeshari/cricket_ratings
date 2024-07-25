from common.data import get_daily_ratings
from common.stats import get_stats_for_list

from datetime import date
from matplotlib import pyplot as plt
from pathlib import Path

import math
import numpy as np

# ['batting', 'bowling', 'allrounder']
TYPE = ''
# ['test', 'odi', 't20']
FORMAT = 't20'

# Graph date range
START_DATE = date(2007, 1, 1)
END_DATE = date(2024, 7, 1)

# Upper and lower bounds of ratings to show
THRESHOLD = 500
MAX_RATING = 1000

# ['', 'rating', 'rank', 'either', 'both']
CHANGED_DAYS_CRITERIA = 'rating'

REMOVE_MISSED_GAME_DROPS = False

# Alternate way to calculate allrounder ratings. Use geometric mean of batting and bowling.
ALLROUNDERS_GEOM_MEAN = True

assert TYPE in ['', 'batting', 'bowling', 'allrounder'], "Invalid TYPE provided"
assert FORMAT in ['', 'test', 'odi', 't20'], "Invalid FORMAT provided"

assert START_DATE < END_DATE, "START_DATE must be earlier than END_DATE"
assert END_DATE <= date.today(), "Future END_DATE requested"

assert MAX_RATING <= 1000, "MAX_RATING must not be greater than 1000"
assert THRESHOLD >= 0 and THRESHOLD < MAX_RATING, \
      "THRESHOLD must be between 0 and MAX_RATING"

assert CHANGED_DAYS_CRITERIA in ['', 'rating', 'rank', 'either', 'both']


def show_aggregate_stats(changes, neg = False):
  print ("Count:\t{c:6d}".format(c = len(changes)))
  print ("Total:\t{t:6d}".format(t = sum(changes)))
  print ("Avg:\t{a:6.2f}".format(a = get_stats_for_list(changes, 'avg')))
  print ("P10:\t{p:6d}".format(p = get_stats_for_list(changes, ('p90' if neg else 'p10'))))
  print ("P25:\t{p:6d}".format(p = get_stats_for_list(changes, ('p75' if neg else 'p25'))))
  print ("P50:\t{p:6d}".format(p = get_stats_for_list(changes, ('p50' if neg else 'p50'))))
  print ("P75:\t{p:6d}".format(p = get_stats_for_list(changes, ('p25' if neg else 'p75'))))
  print ("P90:\t{p:6d}".format(p = get_stats_for_list(changes, ('p10' if neg else 'p90'))))


types_and_formats = []
if TYPE and FORMAT:
  types_and_formats.append((TYPE, FORMAT))
elif TYPE:
  for f in ['test', 'odi', 't20']:
    types_and_formats.append((TYPE, f))
elif FORMAT:
  for t in ['batting', 'bowling']:
    types_and_formats.append((t, FORMAT))
else:
  for f in ['test', 'odi', 't20']:
    for t in ['batting', 'bowling']:
      types_and_formats.append((t, f))

for typ, frmt in types_and_formats:
  print (frmt + '\t' + typ)
  print (str(START_DATE) + ' to ' + str(END_DATE))
  print (str(THRESHOLD) + ' : ' + str(MAX_RATING))

  daily_ratings, _ = get_daily_ratings(typ, frmt, \
                            changed_days_criteria = CHANGED_DAYS_CRITERIA, \
                            allrounders_geom_mean = ALLROUNDERS_GEOM_MEAN)

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
        if last_rating >= THRESHOLD:
          change = rating - last_rating
          if not change == 0:
            all_changes.append((change, rating, d, p))
      last_player_ratings[p] = daily_ratings[d][p]

  all_changes = sorted(all_changes, key = lambda c: c[0], reverse = True)

  daily_gains = [c for (c, _, _, _) in all_changes if c > 0]
  daily_drops = [c for (c, _, _, _) in all_changes if c < 0]

  if REMOVE_MISSED_GAME_DROPS:
    pass

  print ()
  print ("=== GAINS ===")
  show_aggregate_stats(daily_gains)
  print ()
  print ("=== DROPS ===")
  show_aggregate_stats(daily_drops, neg = True)
  print ()
