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

MAX_SIGMA = 3
SIGMA_PERCENTAGES = False

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

print (FORMAT + '\t' + TYPE)
print (str(START_DATE) + ' to ' + str(END_DATE))
print (str(THRESHOLD) + ' : ' + str(BIN_SIZE) + ' : ' + str(MAX_RATING))
if AGGREGATION_WINDOW:
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
    return np.percentile(values, 50)
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

print('\n=== Player count in each bin ===')
h = 'AGG DATE START'
for b in bins:
  h += '\t' + str(b)
print(h)

for d in dates_to_show:
  s = str(d)
  for b in bins:
    bin_ratings = [r for r in aggregate_ratings[d].values() \
                            if r >= b and r < b + BIN_SIZE]
    s += '\t{v}'.format(v = len(bin_ratings))
  print(s)

print('\n=== Mean and sigma values (assuming exponential distribution) ===')
h = 'AGG DATE START\tSTDEV\tTHRSH\tMEAN'
for i in range(1, MAX_SIGMA + 1):
  h += '\tSTD' + str(i)
print(h)

for d in dates_to_show:
  ratings_in_range = [v for v in aggregate_ratings[d].values() \
                          if v >= THRESHOLD and v <= MAX_RATING]
  mean = aggregate_values(sorted(ratings_in_range), 'median')
  stdev = mean - THRESHOLD

  s = str(d) + '\t' + str(int(stdev)) + '\t' + str(THRESHOLD) + '\t' + str(int(mean))
  for i in range(1, MAX_SIGMA + 1):
    s += '\t' + str(int(mean + i * stdev))
  print(s)

print('\n=== Player count in each exponential sigma bin ===')
h = 'AGG DATE START\tTOTAL\tTHRSH\tMEAN'
for i in range(1, MAX_SIGMA + 1):
  h += '\tSTD' + str(i)
print(h)

for d in dates_to_show:
  ratings_in_range = [v for v in aggregate_ratings[d].values() \
                          if v >= THRESHOLD and v <= MAX_RATING]
  mean = aggregate_values(sorted(ratings_in_range), 'median')
  stdev = mean - THRESHOLD

  s = str(d) + '\t' + str(len(ratings_in_range))
  bin_counts = {}
  for t in range(MAX_SIGMA + 2):
    bin_counts[t] = 0
  for r in ratings_in_range:
    r_bin = int((r - THRESHOLD) / stdev)
    if r_bin > MAX_SIGMA + 1:
      r_bin = MAX_SIGMA + 1
    if SIGMA_PERCENTAGES:
      bin_counts[r_bin] += 100 / len(ratings_in_range)
    else:
      bin_counts[r_bin] += 1

  for t in sorted(bin_counts.keys()):
    sigma_value_format = '{c:.2f}' if SIGMA_PERCENTAGES else '{c}'
    s += '\t' + sigma_value_format.format(c = bin_counts[t])
  print(s)

