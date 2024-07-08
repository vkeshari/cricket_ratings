from common.aggregation import aggregate_values, is_aggregation_window_start, \
                                get_aggregate_ratings, get_metrics_by_stops
from common.data import get_daily_ratings
from common.interval_graph import plot_interval_graph
from common.interval_metrics import get_graph_metrics, get_medal_stats, \
                                    get_player_medals, show_top_medals
from common.player_metrics import get_player_stats, show_top_stats
from common.output import string_to_date, readable_name_and_country

from datetime import date, timedelta
from sklearn.preprocessing import power_transform

import numpy as np

DTYPE = 'float'

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

MAX_SIGMA = 3.0
MIN_SIGMA = 0.0
# [0.05, 0.1, 0.2, 0.5]
SIGMA_STEP = 0.05

SIGMA_BINS = round((MAX_SIGMA - MIN_SIGMA) / SIGMA_STEP)

SHOW_BIN_COUNTS = False

SHOW_TOP_STATS = True
TOP_STATS_SORT = ('sum', 'avg')

SHOW_TOP_MEDALS = True
BY_MEDAL_PERCENTAGES = False
AVG_MEDAL_CUMULATIVE_COUNTS = {'gold': 2, 'silver': 5, 'bronze': 10}

SHOW_GRAPH = True
TRIM_EMPTY_ROWS = True
SHOW_MEDALS = True
# ['', 'bronze', 'silver', 'gold']
TRUNCATE_GRAPH_AT = 'bronze'
GRAPH_CUMULATIVES = True

TOP_PLAYERS = 25

# Alternate way to calculate allrounder ratings. Use geometric mean of batting and bowling.
ALLROUNDERS_GEOM_MEAN = True

assert DTYPE in ['int', 'float']
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

assert MAX_SIGMA >= 1.0, "MAX_SIGMA must greater than 1.0"
assert MIN_SIGMA >= 0.0 and MIN_SIGMA < MAX_SIGMA, \
      "MIN_SIGMA must be between 0.0 and MAX_SIGMA"
assert SIGMA_STEP in [0.05, 0.1, 0.2, 0.5], "Invalid SIGMA_STEP provided"

assert not AVG_MEDAL_CUMULATIVE_COUNTS.keys() ^ {'gold', 'silver', 'bronze'}, \
      "AVG_MEDAL_CUMULATIVE_COUNTS keys must be gold silver and bronze"
for amcc in AVG_MEDAL_CUMULATIVE_COUNTS.values():
  assert amcc > 0, "All values in AVG_MEDAL_CUMULATIVE_COUNTS must be positive"

if SHOW_MEDALS:
  assert SHOW_GRAPH, "SHOW_GRAPH must be enabled if SHOW_MEDALS is enabled"
assert TRUNCATE_GRAPH_AT in ['', 'bronze', 'silver', 'gold']
if TRUNCATE_GRAPH_AT:
  assert SHOW_MEDALS, "SHOW_MEDALS must be enabled if either of" \
                      + " TRIM_EMPTY_ROWS or TRUNCATE_GRAPH_AT is enabled"

if TOP_STATS_SORT:
  assert SHOW_TOP_STATS, "SHOW_TOP_STATS must be enabled if TOP_STATS_SORT is enabled"
  assert not set(TOP_STATS_SORT) - {'span', 'avg', 'max', 'sum'}, \
      "Invalid sort parameter in TOP_STATS_SORT"

assert TOP_PLAYERS > 5, "TOP_PLAYERS must be at least 5"

print (FORMAT + '\t' + TYPE)
print (str(START_DATE) + ' to ' + str(END_DATE))
print (str(THRESHOLD) + ' : ' + str(MAX_RATING))
print (AGGREGATION_WINDOW + ' / ' + PLAYER_AGGREGATE)

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

for i, d in enumerate(dates_to_show):
  if d.year in SKIP_YEARS:
    del dates_to_show[i]
if dates_to_show[-1] == END_DATE:
  dates_to_show.pop()


def get_normalized_ratings(aggregate_ratings, dates_to_show):
  normalized_ratings = {}

  for d in dates_to_show:
    day_ratings = aggregate_ratings[d]
    day_ratings = {p: (r - THRESHOLD) / (MAX_RATING - THRESHOLD) \
                              for (p, r) in day_ratings.items() if r >= THRESHOLD}
    day_ratings = dict(sorted(day_ratings.items(), key = lambda item: item[1], reverse = True))

    day_vals = np.array(list(day_ratings.values()))
    normalized_vals = power_transform(day_vals.reshape(-1, 1)).reshape(1, -1).flatten()

    normalized_ratings[d] = {}
    for i, p in enumerate(day_ratings.keys()):
      normalized_ratings[d][p] = normalized_vals[i]

  return normalized_ratings

aggregate_ratings = get_normalized_ratings(aggregate_ratings, dates_to_show)

if SHOW_TOP_STATS:
  player_stats = get_player_stats(aggregate_ratings, dates_to_show, \
                                  top_players = TOP_PLAYERS)
  show_top_stats(player_stats, sort_by = TOP_STATS_SORT, \
                  top_players = TOP_PLAYERS, dtype = DTYPE)

if SHOW_TOP_MEDALS or SHOW_GRAPH:
  sigma_stops = np.linspace(MIN_SIGMA, MAX_SIGMA, SIGMA_BINS + 1)
  actual_sigma_stops = sigma_stops[ : -1]

  metrics_bins, player_counts_by_step, player_periods = \
          get_metrics_by_stops(aggregate_ratings, stops = sigma_stops, \
                                dates = dates_to_show, \
                                by_percentage = BY_MEDAL_PERCENTAGES, \
                                show_bin_counts = SHOW_BIN_COUNTS, \
                              )

  reversed_stops = list(reversed(actual_sigma_stops))

  graph_metrics = get_graph_metrics(metrics_bins, stops = reversed_stops, \
                                    dates = dates_to_show, cumulatives = GRAPH_CUMULATIVES)


  medal_stats = get_medal_stats(graph_metrics, stops = reversed_stops, \
                                avg_medal_cumulative_counts = AVG_MEDAL_CUMULATIVE_COUNTS)

  player_medals = get_player_medals(player_counts_by_step, medal_stats)


if SHOW_TOP_MEDALS:
  show_top_medals(player_medals, player_periods, top_players = TOP_PLAYERS, \
                    by_percentage = BY_MEDAL_PERCENTAGES)

if SHOW_GRAPH:
  graph_annotations = {'TYPE': TYPE, 'FORMAT': FORMAT, \
                        'START_DATE': START_DATE, 'END_DATE': END_DATE, \
                        'AGGREGATION_WINDOW': AGGREGATION_WINDOW, \
                        'PLAYER_AGGREGATE': PLAYER_AGGREGATE, \
                        'LABEL_KEY': 'std dev', 'LABEL_TEXT': 'Gaussian std devs', \
                        'DTYPE': DTYPE, \
                        }

  yparams_max = MAX_SIGMA
  if TRIM_EMPTY_ROWS:
    for i, s in enumerate(reversed_stops):
      if graph_metrics['lines'][i][1] == 0:
        yparams_max = s
      else:
        break
  if SHOW_MEDALS and TRUNCATE_GRAPH_AT:
    yparams_min = medal_stats[TRUNCATE_GRAPH_AT]['threshold'] - SIGMA_STEP
  else:
    yparams_min = MIN_SIGMA
  graph_yparams = {'min': yparams_min, 'max': yparams_max, 'step': SIGMA_STEP}

  plot_interval_graph(graph_metrics, stops = reversed_stops, \
                      annotations = graph_annotations, yparams = graph_yparams, \
                      medal_stats = medal_stats, show_medals = SHOW_MEDALS)

