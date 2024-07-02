# DEPRECATED
import sys
sys.exit("DEPRECATED: Use top_exp_graph.py")

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
START_DATE = date(2021, 1, 1)
END_DATE = date(2024, 1, 1)
SKIP_YEARS = list(range(1913, 1921)) + list(range(1940, 1946)) + [2020]

# Upper and lower bounds of ratings to show
THRESHOLD = 0
MAX_RATING = 1000

# Aggregation
# ['', 'monthly', 'quarterly', 'halfyearly', 'yearly', 'decadal']
AGGREGATION_WINDOW = 'yearly'
# ['', 'avg', 'median', 'min', 'max', 'first', 'last']
PLAYER_AGGREGATE = 'max'

TOP_PLAYERS = 25
THRESHOLD_RELATIVE = False

RATIO_STOPS = [0.79, 0.86, 0.92, 1]

SHOW_METRICS = False
SHOW_BIN_COUNTS = False
BY_MEDAL_PERCENTAGES = False

# Alternate way to calculate allrounder ratings. Use geometric mean of batting and bowling.
ALLROUNDERS_GEOM_MEAN = True

assert TYPE in ['batting', 'bowling', 'allrounder'], "Invalid TYPE provided"
assert FORMAT in ['test', 'odi', 't20'], "Invalid FORMAT provided"
assert START_DATE < END_DATE, "START_DATE must be earlier than END_DATE"
assert END_DATE <= date.today(), "Future END_DATE requested"

assert THRESHOLD >= 0, "THRESHOLD must not be negative"
assert MAX_RATING <= 1000, "MAX_RATING must not be greater than 1000"

assert AGGREGATION_WINDOW in ['monthly', 'quarterly', 'halfyearly', 'yearly', 'decadal'], \
      "Invalid AGGREGATION_WINDOW provided"
assert PLAYER_AGGREGATE in ['avg', 'median', 'min', 'max', 'first', 'last'], \
      "Invalid PLAYER_AGGREGATE provided"
assert TOP_PLAYERS >= 5, "TOP_PLAYERS must be at least 5"

assert len(RATIO_STOPS) == 4, "RATIO_STOPS must have length 4"
assert RATIO_STOPS[-1] == 1.0, "Last value of RATIO_STOPS must be 1.0"
for r in RATIO_STOPS:
  assert r > 0.0 and r <= 1.0, "Each value in RATIO_STOPS must be in (0, 1]"

def strictly_increasing(l):
  if len(l) == 1:
    return True
  for i, v in enumerate(l):
    if i == 0:
      continue
    if v <= l[i - 1]:
      return False
  return True
assert strictly_increasing(RATIO_STOPS), "RATIO_STOPS must be strictly increasing"

print (FORMAT + '\t' + TYPE)
print (str(START_DATE) + ' to ' + str(END_DATE))
print (str(THRESHOLD) + ' : ' + str(MAX_RATING))
print (AGGREGATION_WINDOW + ' / ' + PLAYER_AGGREGATE)

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

  return daily_ratings

daily_ratings = get_daily_ratings()
print("Daily ratings data built for " + str(len(daily_ratings)) + " days" )

first_date = min(daily_ratings.keys())
last_date = max(daily_ratings.keys())

def is_aggregation_window_start(d):
  if d.year in SKIP_YEARS:
    return False
  return AGGREGATION_WINDOW == 'monthly' and d.day == 1 \
      or AGGREGATION_WINDOW == 'quarterly' and d.day == 1 and d.month in [1, 4, 7, 10] \
      or AGGREGATION_WINDOW == 'halfyearly' and d.day == 1 and d.month in [1, 7] \
      or AGGREGATION_WINDOW == 'yearly' and d.day == 1 and d.month == 1 \
      or AGGREGATION_WINDOW == 'decadal' and d.day == 1 and d.month == 1 \
                                        and d.year % 10 == 1

def aggregate_values(values, agg_type):
  if agg_type == 'avg':
    return np.average(values)
  if agg_type == 'median':
    return np.percentile(values, 50, method = 'nearest')
  if agg_type == 'min':
    return min(values)
  if agg_type == 'max':
    return max(values)
  if agg_type == 'first':
    return values[0]
  if agg_type == 'last':
    return values[-1]

def get_aggregate_ratings(daily_ratings):
  if not AGGREGATION_WINDOW:
    return daily_ratings

  aggregate_ratings = {}

  if PLAYER_AGGREGATE:
    bucket_values = {}
    last_window_start = first_date
    for d in daily_ratings:
      if d not in aggregate_ratings:
        aggregate_ratings[d] = {}
      if d == last_date or is_aggregation_window_start(d):
        for p in bucket_values:
          aggregate_ratings[last_window_start][p] = \
                  aggregate_values(bucket_values[p], PLAYER_AGGREGATE)
        bucket_values = {}
        last_window_start = d
      else:
        aggregate_ratings[d] = aggregate_ratings[last_window_start]

      for p in daily_ratings[d]:
        if p not in bucket_values:
          bucket_values[p] = []
        bucket_values[p].append(daily_ratings[d][p])

  return aggregate_ratings

aggregate_ratings = get_aggregate_ratings(daily_ratings)
print(AGGREGATION_WINDOW + " aggregate ratings built")

dates_to_show = []
d = first_date
while d <= last_date:
  if d >= START_DATE and d <= END_DATE and is_aggregation_window_start(d):
    dates_to_show.append(d)
  d += ONE_DAY

metrics_bins = {}
actual_ratio_stops = RATIO_STOPS[ : -1]
for r in actual_ratio_stops:
  metrics_bins[r] = []

if SHOW_BIN_COUNTS:
  print('\n=== Player count in each rating ratio bin ===')
  h = 'AGG START DATE'
  for b in actual_ratio_stops:
    h += '\t' + '{b:.2f}'.format(b = b)
  print(h)

player_medals = {}
player_periods = {}

for d in dates_to_show:
  ratings_in_range = {k: v for k, v in aggregate_ratings[d].items() \
                      if v >= THRESHOLD and v <= MAX_RATING}
  
  max_rating = max(ratings_in_range.values())

  bin_counts = [0] * len(RATIO_STOPS)
  bin_players = []
  for r in RATIO_STOPS:
    bin_players.append([])
  for p in ratings_in_range:
    rating = ratings_in_range[p]
    if p not in player_periods:
      player_periods[p] = 0
    player_periods[p] += 1
    if THRESHOLD_RELATIVE:
      rating_ratio = (rating - THRESHOLD) / (max_rating - THRESHOLD)
    else:
      rating_ratio = rating / max_rating
    if rating_ratio < RATIO_STOPS[0]:
      continue
    for i, r in enumerate(RATIO_STOPS):
      if rating_ratio < r:
        bin_counts[i - 1] += 1
        bin_players[i - 1].append(p)
        break
      if rating_ratio == r:
        bin_counts[i] += 1
        bin_players[i].append(p)
        break
  bin_counts[-2] += bin_counts[-1]
  bin_players[-2] += bin_players[-1]

  for i, r in enumerate(actual_ratio_stops):
    metrics_bins[r].append(bin_counts[i])

  for i, r in enumerate(actual_ratio_stops):
    for p in bin_players[i]:
      if p not in player_medals:
        player_medals[p] = {}
        for rs in actual_ratio_stops:
          player_medals[p][rs] = 0
      player_medals[p][r] += 1

if BY_MEDAL_PERCENTAGES:
  for p in player_medals:
    for r in player_medals[p]:
      player_medals[p][r] = 100 * player_medals[p][r] / player_periods[p]

  if SHOW_BIN_COUNTS:
    s = str(d)
    for b in bin_counts[ : -1]:
      s += '\t' + str(b)
    print (s)

for r in actual_ratio_stops:
  player_medals = dict(sorted(player_medals.items(),
                                key = lambda item: item[1][r], reverse = True))


if SHOW_METRICS:
  print('\n=== Metrics for player count in each rating ratio bin ===')
  percentiles = [10, 50, 90]
  h = 'METRIC'
  for r in reversed(metrics_bins):
    h += '\t' + str(r)
  print(h)

  for p in percentiles:
    s = 'P' + str(p)
    for r in reversed(metrics_bins):
      s += '\t' + str(int(np.percentile(metrics_bins[r], p, method = 'nearest')))
    print (s)

  print()

  s = 'AVG'
  for r in reversed(metrics_bins):
    s += '\t' + '{v:.2f}'.format(v = np.average(metrics_bins[r]))
  print (s)

  s = 'SUM'
  for r in reversed(metrics_bins):
    s += '\t' + str(sum(metrics_bins[r]))
  print (s)

  print()

  cumulatives = {}
  cum_total = 0
  cum_avg = 0
  for r in reversed(metrics_bins):
    cumulatives[r] = {}
    cum_total += sum(metrics_bins[r])
    cumulatives[r]['sum'] = cum_total
    cum_avg += np.average(metrics_bins[r])
    cumulatives[r]['avg'] = cum_avg

  s = 'C_AVG'
  for r in reversed(metrics_bins):
    s += '\t' + '{v:.2f}'.format(v = cumulatives[r]['avg'])
  print(s)

  s = 'C_SUM'
  for r in reversed(metrics_bins):
    s += '\t' + str(cumulatives[r]['sum'])
  print(s)

def readable_name(p):
  sep = p.find('_')
  return p[sep+1:].split('.')[0].replace('_', ' ')

def country(p):
  return p.split('_')[0]

def full_readable_name(p):
  return readable_name(p) + ' (' + country(p) + ')'

print('\n=== Top ' + str(TOP_PLAYERS) + ' Players ===')
print('SPAN,\tMEDALS,\tGOLD,\tSILVER,\tBRONZE,\tPLAYER NAME')

for i, p in enumerate(player_medals):
  s = str(player_periods[p]) + ','
  total_medals = sum(player_medals[p].values())
  if BY_MEDAL_PERCENTAGES:
    s += '\t{v:.2f}'.format(v = total_medals) + ','
  else:
    s += '\t' + str(total_medals) + ','
  for r in reversed(actual_ratio_stops):
    if BY_MEDAL_PERCENTAGES:
      s += '\t{v:.2f}'.format(v = player_medals[p][r]) + ','
    else:
      s += '\t' + str(player_medals[p][r]) + ','
  s += '\t' + full_readable_name(p)
  print (s)

  if i >= TOP_PLAYERS:
    break
