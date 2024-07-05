from common.aggregation import aggregate_values, \
                                get_aggregate_ratings, \
                                is_aggregation_window_start
from common.data import get_daily_ratings
from common.interval_graph import plot_interval_graph
from common.interval_metrics import get_graph_metrics, get_medal_stats, \
                                    get_player_medals, show_top_players
from common.output import string_to_date, readable_name_and_country

from datetime import date, timedelta

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

# Aggregation
# ['', 'monthly', 'quarterly', 'halfyearly', 'yearly', 'decadal']
AGGREGATION_WINDOW = 'yearly'
# ['', 'avg', 'median', 'min', 'max', 'first', 'last']
PLAYER_AGGREGATE = 'max'
# ['', 'avg', 'median', 'min', 'max', 'first', 'last']
BIN_AGGREGATE = 'avg'

EXP_BIN_SIZE = 10

MAX_SIGMA = 3.0
MIN_SIGMA = 0.0
# [0.05, 0.1, 0.2, 0.5]
SIGMA_STEP = 0.1

SIGMA_BINS = round((MAX_SIGMA - MIN_SIGMA) / SIGMA_STEP)

GRAPH_CUMULATIVES = True
BY_MEDAL_PERCENTAGES = False

AVG_MEDAL_CUMULATIVE_COUNTS = {'gold': 2, 'silver': 5, 'bronze': 10}

SHOW_BIN_COUNTS = False
SHOW_GRAPH = True
SHOW_MEDALS = True
TRUNCATE_AT_BRONZE = True

SHOW_TOP_PLAYERS = True
TOP_PLAYERS = 25

EPOCH = date(1900, 1, 1)

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

assert AGGREGATION_WINDOW in ['monthly', 'quarterly', 'halfyearly', 'yearly', 'decadal'], \
      "Invalid AGGREGATION_WINDOW provided"
assert PLAYER_AGGREGATE in ['avg', 'median', 'min', 'max', 'first', 'last'], \
      "Invalid PLAYER_AGGREGATE provided"
assert BIN_AGGREGATE in ['avg', 'median', 'min', 'max', 'first', 'last'], \
      "Invalid BIN_AGGREGATE provided"

assert EXP_BIN_SIZE >= 10, "EXP_BIN_SIZE must be at least 10"
assert MAX_SIGMA >= 1.0, "MAX_SIGMA must greater than 1.0"
assert MIN_SIGMA >= 0.0 and MIN_SIGMA < MAX_SIGMA, \
      "MIN_SIGMA must be between 0.0 and MAX_SIGMA"
assert SIGMA_STEP in [0.05, 0.1, 0.2, 0.5], "Invalid SIGMA_STEP provided"

assert not AVG_MEDAL_CUMULATIVE_COUNTS.keys() ^ {'gold', 'silver', 'bronze'}, \
    'AVG_MEDAL_CUMULATIVE_COUNTS keys must be gold silver and bronze'
for amcc in AVG_MEDAL_CUMULATIVE_COUNTS.values():
  assert amcc > 0, "All values in AVG_MEDAL_CUMULATIVE_COUNTS must be positive"

assert TOP_PLAYERS > 5, "TOP_PLAYERS must be at least 5"

if TRUNCATE_AT_BRONZE:
  assert SHOW_MEDALS, "SHOW_MEDALS must be enabled if TRUNCATE_AT_BRONZE is enabled"

print (FORMAT + '\t' + TYPE)
print (str(START_DATE) + ' to ' + str(END_DATE))
print (str(THRESHOLD) + ' : ' + str(MAX_RATING))
print (AGGREGATION_WINDOW + ' / ' + BIN_AGGREGATE + ' / ' + PLAYER_AGGREGATE)

daily_ratings, _ = get_daily_ratings(TYPE, FORMAT, \
                          changed_days_criteria = CHANGED_DAYS_CRITERIA, \
                          agg_window = AGGREGATION_WINDOW, \
                          allrounders_geom_mean = ALLROUNDERS_GEOM_MEAN)

first_date = min(daily_ratings.keys())
last_date = max(daily_ratings.keys())

dates_to_show = []
d = first_date
while d <= last_date:
  if d >= START_DATE and d <= END_DATE \
          and is_aggregation_window_start(d, AGGREGATION_WINDOW):
    dates_to_show.append(d)
  d += ONE_DAY

bin_by_date = np.searchsorted(dates_to_show, list(daily_ratings.keys()), side = 'right')
date_to_bucket = {}
for i, d in enumerate(daily_ratings.keys()):
  if bin_by_date[i] > 0:
    date_to_bucket[d] = dates_to_show[bin_by_date[i] - 1]

aggregate_ratings = get_aggregate_ratings(daily_ratings, agg_dates = dates_to_show, \
                                          date_to_agg_date = date_to_bucket, \
                                          aggregation_window = AGGREGATION_WINDOW, \
                                          player_aggregate = PLAYER_AGGREGATE)


def get_exp_medians(daily_ratings):
  if not AGGREGATION_WINDOW:
    return daily_ratings

  exp_bin_stops = list(range(THRESHOLD, MAX_RATING, EXP_BIN_SIZE)) + [MAX_RATING]

  aggregate_buckets = {d: [] for d in dates_to_show}
  for d in daily_ratings:
    if not d in date_to_bucket:
      continue
    bucket = date_to_bucket[d]
    distribution_for_date = np.histogram(list(daily_ratings[d].values()), \
                                            bins = exp_bin_stops
                                          )[0]
    aggregate_buckets[bucket].append(distribution_for_date)

  for d in aggregate_buckets:
    for dist in aggregate_buckets[d]:
      total_count = sum(dist)
      for i, val in enumerate(dist):
        dist[i] = val * 100 / total_count

  aggregated_buckets = {d: [] for d in dates_to_show}
  num_bins = len(exp_bin_stops) - 1

  for d in aggregate_buckets:
    aggregate_buckets[d] = list(zip(*aggregate_buckets[d]))

  for d in aggregate_buckets:
    for i in range(num_bins):
      aggregated_buckets[d].append(aggregate_values(aggregate_buckets[d][i], BIN_AGGREGATE))

  exp_medians = {}

  for d in aggregated_buckets:
    bin_vals = aggregated_buckets[d]
    median_count = sum(bin_vals) / 2

    cum_val = 0
    for i, v in enumerate(bin_vals):
      cum_val += v
      if cum_val >= median_count:
        exp_medians[d] = exp_bin_stops[i]
        break

  return exp_medians

exp_medians = get_exp_medians(daily_ratings)
print(AGGREGATION_WINDOW + " exp medians built")

metrics_bins = {}
sigma_stops = np.linspace(MIN_SIGMA, MAX_SIGMA, SIGMA_BINS + 1)
actual_sigma_stops = sigma_stops[ : -1]
for r in actual_sigma_stops:
  metrics_bins[r] = []

if SHOW_BIN_COUNTS:
  print('\n=== Player count in each rating sigma bin ===')
  h = 'AGG START DATE'
  for b in actual_sigma_stops:
    h += '\t' + '{b:.2f}'.format(b = b)
  print(h)

player_counts_by_step = {}
player_periods = {}

for i, d in enumerate(dates_to_show):
  if d.year in SKIP_YEARS:
    del dates_to_show[i]
if dates_to_show[-1] == END_DATE:
  dates_to_show.pop()

for d in dates_to_show:
  ratings_in_range = {k: v for k, v in aggregate_ratings[d].items() \
                      if v >= THRESHOLD and v <= MAX_RATING}
  
  median_val = exp_medians[d]

  bin_counts = [0] * len(sigma_stops)
  bin_players = []
  for r in sigma_stops:
    bin_players.append([])
  for p in ratings_in_range:
    rating = ratings_in_range[p]
    if p not in player_periods:
      player_periods[p] = 0
    player_periods[p] += 1

    rating_sigma = (rating - THRESHOLD) / (median_val - THRESHOLD)
    if rating_sigma < sigma_stops[0]:
      continue
    for i, r in enumerate(sigma_stops):
      if rating_sigma < r:
        bin_counts[i - 1] += 1
        bin_players[i - 1].append(p)
        break
      if rating_sigma == r:
        bin_counts[i] += 1
        bin_players[i].append(p)
        break
  bin_counts[-2] += bin_counts[-1]
  bin_players[-2] += bin_players[-1]

  for i, r in enumerate(actual_sigma_stops):
    metrics_bins[r].append(bin_counts[i])

  for i, r in enumerate(actual_sigma_stops):
    for p in bin_players[i]:
      if p not in player_counts_by_step:
        player_counts_by_step[p] = {}
        for rs in actual_sigma_stops:
          player_counts_by_step[p][rs] = 0
      player_counts_by_step[p][r] += 1

  if BY_MEDAL_PERCENTAGES:
    for p in player_counts_by_step:
      for r in player_counts_by_step[p]:
        player_counts_by_step[p][r] = 100 * player_counts_by_step[p][r] / player_periods[p]

  if SHOW_BIN_COUNTS:
    s = str(d)
    for b in bin_counts[ : -1]:
      s += '\t' + str(b)
    print (s)


reversed_stops = list(reversed(actual_sigma_stops))

graph_metrics = get_graph_metrics(metrics_bins, stops = reversed_stops, \
                                  dates = dates_to_show, cumulatives = GRAPH_CUMULATIVES)


medal_stats = get_medal_stats(graph_metrics, stops = reversed_stops, \
                              avg_medal_cumulative_counts = AVG_MEDAL_CUMULATIVE_COUNTS)

player_medals = get_player_medals(player_counts_by_step, medal_stats)


if SHOW_TOP_PLAYERS:
  show_top_players(player_medals, player_periods, top_players = TOP_PLAYERS, \
                    by_percentage = BY_MEDAL_PERCENTAGES)

if SHOW_GRAPH:
  graph_annotations = {'TYPE': TYPE, 'FORMAT': FORMAT, \
                        'START_DATE': START_DATE, 'END_DATE': END_DATE, \
                        'AGGREGATION_WINDOW': AGGREGATION_WINDOW, \
                        'PLAYER_AGGREGATE': PLAYER_AGGREGATE, \
                        'LABEL_KEY': 'std dev', 'LABEL_TEXT': 'Exponential std devs', \
                        'DTYPE': 'float', \
                        }

  if SHOW_MEDALS and TRUNCATE_AT_BRONZE:
    yparams_min = medal_stats['bronze']['threshold'] - SIGMA_STEP
  else:
    yparams_min = MIN_SIGMA
  graph_yparams = {'min': yparams_min, 'max': MAX_SIGMA, 'step': SIGMA_STEP}

  plot_interval_graph(graph_metrics, stops = reversed_stops, \
                      annotations = graph_annotations, yparams = graph_yparams, \
                      medal_stats = medal_stats, show_medals = SHOW_MEDALS)
