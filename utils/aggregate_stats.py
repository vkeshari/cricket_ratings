import math

from datetime import date, timedelta, datetime
from os import listdir
import numpy as np
from scipy import optimize

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
BIN_AGGREGATE = 'avg'

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
assert BIN_AGGREGATE in ['avg', 'median', 'min', 'max', 'first', 'last'], \
      "Invalid PLAYER_AGGREGATE provided"

print (FORMAT + '\t' + TYPE)
print (str(START_DATE) + ' to ' + str(END_DATE))
print (str(THRESHOLD) + ' : ' + str(BIN_SIZE) + ' : ' + str(MAX_RATING))
print (AGGREGATION_WINDOW + ' / ' + BIN_AGGREGATE)

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

  bucket_values = {}
  last_window_start = first_date
  for d in daily_ratings:
    if d not in aggregate_ratings:
      aggregate_ratings[d] = {}
    if d == last_date or is_aggregation_window_start(d):
      for b in bucket_values:
        aggregate_ratings[last_window_start][b] = \
                aggregate_values(bucket_values[b], BIN_AGGREGATE)
      bucket_values = {}
      last_window_start = d
    else:
      aggregate_ratings[d] = aggregate_ratings[last_window_start]

    day_bin_counts = {}
    day_player_total = 0 # used to normalize
    for p in daily_ratings[d]:
      player_rating = daily_ratings[d][p]
      player_bin_number = int((player_rating - THRESHOLD) / BIN_SIZE)
      if player_bin_number < 0:
        continue
      player_bin = THRESHOLD + player_bin_number * BIN_SIZE

      if player_bin not in day_bin_counts:
        day_bin_counts[player_bin] = 0
      day_bin_counts[player_bin] += 1
      day_player_total += 1

    for b in day_bin_counts:
      if b not in bucket_values:
        bucket_values[b] = []
      bucket_values[b].append(day_bin_counts[b] / day_player_total)

  return aggregate_ratings

aggregate_ratings = get_aggregate_ratings(daily_ratings)
print(AGGREGATION_WINDOW + ' ' + BIN_AGGREGATE + " aggregate ratings built")

h = 'AGG DATE START'
for b in bins:
  h += '\t' + str(b)
print(h)
d = first_date
while d <= last_date:
  if d >= START_DATE and d <= END_DATE and is_aggregation_window_start(d):
    s = str(d)
    for b in bins:
      if b not in aggregate_ratings[d]:
        aggregate_ratings[d][b] = 0
      s += '\t{v:.2f}'.format(v = aggregate_ratings[d][b] * 100)
    print(s)
  d += ONE_DAY

def exp_func(x, a, b):
  return a * np.exp(-x / b)

print('AGG DATE START\tOPT PARAMS')
d = first_date
while d <= last_date:
  if d >= START_DATE and d <= END_DATE and is_aggregation_window_start(d):
    s = str(d)
    for b in bins:
      if b not in aggregate_ratings[d]:
        aggregate_ratings[d][b] = 0

    xs = [((b + BIN_SIZE / 2 ) - THRESHOLD) / (MAX_RATING - THRESHOLD) for b in bins]
    ys = [item[1] for item in sorted(aggregate_ratings[d].items())]
    (a, b), _ = optimize.curve_fit(exp_func, xs, ys)

    mean = THRESHOLD + (MAX_RATING - THRESHOLD) * b
    sig1 = THRESHOLD + (MAX_RATING - THRESHOLD) * 2 * b
    sig2 = THRESHOLD + (MAX_RATING - THRESHOLD) * 3 * b
    sig3 = THRESHOLD + (MAX_RATING - THRESHOLD) * 4 * b
    s += ('\ta: {a:.2f}\tb: {b:.2f}\tmean: {m:.2f}' \
              + '\tsig1: {s1}\tsig2: {s2}\tsig3: {s3}') \
          .format(a = a, b = b, m = mean, s1 = int(sig1), s2 = int(sig2), s3 = int(sig3))
    print(s)
  d += ONE_DAY
