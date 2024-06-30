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

# Upper and lower bounds of ratings to show
THRESHOLD = 500
MAX_RATING = 1000
BIN_SIZE = 50

# Aggregation
# ['', 'monthly', 'quarterly', 'halfyearly', 'yearly', 'decadal']
AGGREGATION_WINDOW = 'quarterly'
# ['', 'avg', 'median', 'min', 'max', 'first', 'last']
PLAYER_AGGREGATE = 'max'

MIN_RATIO = 0.05
# [0.025, 0.05, 0.1]
RATIO_STEP = 0.05

RATIO_STOPS = [0.5, 0.7, 0.9, 1.0]

THRESHOLD_RELATIVE = True
SHOW_PERCENTAGES = False

VERBOSE = True

# Alternate way to calculate allrounder ratings. Use geometric mean of batting and bowling.
ALLROUNDERS_GEOM_MEAN = True

assert TYPE in ['batting', 'bowling', 'allrounder'], "Invalid TYPE provided"
assert FORMAT in ['test', 'odi', 't20'], "Invalid FORMAT provided"
assert START_DATE < END_DATE, "START_DATE must be earlier than END_DATE"
assert END_DATE <= date.today(), "Future END_DATE requested"

assert THRESHOLD >= 0, "THRESHOLD must not be negative"
assert MAX_RATING <= 1000, "MAX_RATING must not be greater than 1000"
assert BIN_SIZE >= 10, "BIN_SIZE must be at least 10"
assert (MAX_RATING - THRESHOLD) % BIN_SIZE == 0, "BIN_SIZE must split ratings range evenly"

assert AGGREGATION_WINDOW in ['monthly', 'quarterly', 'halfyearly', 'yearly', 'decadal'], \
      "Invalid AGGREGATION_WINDOW provided"
assert PLAYER_AGGREGATE in ['avg', 'median', 'min', 'max', 'first', 'last'], \
      "Invalid PLAYER_AGGREGATE provided"

assert MIN_RATIO > 0, "MIN_RATIO must be greater than 0.5"
assert RATIO_STEP in [0.025, 0.05, 0.1], "Invalid RATIO_STEP provided"

if RATIO_STOPS:
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
print (str(THRESHOLD) + ' : ' + str(BIN_SIZE) + ' : ' + str(MAX_RATING))
print (AGGREGATION_WINDOW + ' / ' + PLAYER_AGGREGATE)

def string_to_date(s):
  dt = datetime.strptime(s, '%Y%m%d')
  return date(dt.year, dt.month, dt.day)

def readable_name(p):
  sep = p.find('_')
  return p[sep+1:].split('.')[0].replace('_', ' ')

def country(p):
  return p.split('_')[0]

def full_readable_name(p):
  return readable_name(p) + ' (' + country(p) + ')'

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
bins = range(THRESHOLD, MAX_RATING, BIN_SIZE)

def is_aggregation_window_start(d):
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

if VERBOSE:

  print('\n=== Player count in each rating bin ===')
  h = 'AGG DATE START'
  for b in bins:
    h += '\t' + str(b)
  h += '\tMax'
  print(h)
  d = first_date
  for d in dates_to_show:
    s = str(d)
    for b in bins:
      bin_ratings = [r for r in aggregate_ratings[d].values() \
                              if r >= b and r < b + BIN_SIZE]
      s += '\t{v}'.format(v = len(bin_ratings))
    max_rating = max(aggregate_ratings[d].values())
    s += '\t' + str(max_rating)
    print(s)

  print('\n=== Player count in each rating ratio bin (by step) ===')
  h = 'AGG START DATE'
  num_bins = round((1.0 - MIN_RATIO) / RATIO_STEP)
  bin_stops = np.linspace(MIN_RATIO, 1.0, num_bins + 1)
  for b in bin_stops:
    h += '\t' + '{b:.2f}'.format(b = b)
  print(h)

  for d in dates_to_show:
    ratings_in_range = [v for v in aggregate_ratings[d].values() \
                        if v >= THRESHOLD and v <= MAX_RATING]
    
    max_rating = max(ratings_in_range)
    total_players = len(ratings_in_range)

    bin_counts = [0] * len(bin_stops)
    for r in ratings_in_range:
      if THRESHOLD_RELATIVE:
        rating_ratio = (r - THRESHOLD) / (max_rating - THRESHOLD)
      else:
        rating_ratio = r / max_rating
      if rating_ratio < bin_stops[0]:
        continue
      for i, b in enumerate(bin_stops):
        if rating_ratio < b:
          bin_counts[i - 1] += 1
          break
        if rating_ratio == b:
          bin_counts[i] += 1
          break

    s = str(d)
    for b in bin_counts:
      if SHOW_PERCENTAGES:
        s += '\t' + '{v:.2f}'.format(v = b * 100 / total_players)
      else:
        s += '\t' + str(b)
    print (s)

if VERBOSE:
  print('\n=== Player count in each rating ratio bin (provided) ===')
  h = 'AGG START DATE'
  for b in RATIO_STOPS:
    h += '\t' + '{b:.2f}'.format(b = b)
  print(h)

super_bins = {}
for r in RATIO_STOPS[ : -1]:
  super_bins[r] = []

for d in dates_to_show:
  ratings_in_range = [v for v in aggregate_ratings[d].values() \
                      if v >= THRESHOLD and v <= MAX_RATING]
  
  max_rating = max(ratings_in_range)
  total_players = len(ratings_in_range)

  bin_counts = [0] * len(RATIO_STOPS)
  for r in ratings_in_range:
    if THRESHOLD_RELATIVE:
      rating_ratio = (r - THRESHOLD) / (max_rating - THRESHOLD)
    else:
      rating_ratio = r / max_rating
    if rating_ratio < RATIO_STOPS[0]:
      continue
    for i, r in enumerate(RATIO_STOPS):
      if rating_ratio < r:
        bin_counts[i - 1] += 1
        break
      if rating_ratio == r:
        bin_counts[i] += 1
        break
  bin_counts[-2] += bin_counts[-1]

  for i, r in enumerate(super_bins.keys()):
    super_bins[r].append(bin_counts[i])

  if VERBOSE:
    s = str(d)
    for b in bin_counts:
      if SHOW_PERCENTAGES:
        s += '\t' + '{v:.2f}'.format(v = b * 100 / total_players)
      else:
        s += '\t' + str(b)
    print (s)

print('\n=== Metrics for player count in each rating ratio bin (provided) ===')
percentiles = [10, 50, 90]
h = 'METRIC'
for r in super_bins:
  h += '\t' + str(r)
print(h)

for p in percentiles:
  s = 'P' + str(p)
  for r in super_bins:
    s += '\t' + str(int(np.percentile(super_bins[r], p, method = 'nearest')))
  print (s)
s = 'AVG'
for r in super_bins:
  s += '\t' + '{v:.2f}'.format(v = np.average(super_bins[r]))
print (s)
