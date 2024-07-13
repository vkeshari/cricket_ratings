from common.aggregation import is_aggregation_window_start, \
                                get_aggregation_dates, date_to_aggregation_date, \
                                get_aggregate_ratings, get_metrics_by_stops, \
                                VALID_AGGREGATIONS
from common.data import get_daily_ratings
from common.interval_graph import plot_interval_graph
from common.interval_metrics import get_graph_metrics, get_medal_stats, \
                                    get_player_medals, show_top_medals
from common.player_metrics import get_player_stats, show_top_stats
from common.output import string_to_date, readable_name_and_country
from common.stats import VALID_STATS

from datetime import date, timedelta

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
# See common.aggregation.VALID_AGGREGATIONS for possible windows
AGGREGATION_WINDOW = 'yearly'
# See common.stats.VALID_STATS for possible aggregate stats
PLAYER_AGGREGATE = 'max'

THRESHOLD_RELATIVE = False

MAX_RATIO = 1.0
MIN_RATIO = 0.7
# [0.01, 0.02, 0.05, 0.1]
RATIO_STEP = 0.01

RATIO_BINS = round((MAX_RATIO - MIN_RATIO) / RATIO_STEP)

SHOW_BIN_COUNTS = False

SHOW_TOP_STATS = True
TOP_STATS_SORT = ('max', 'avg')

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

assert AGGREGATION_WINDOW in VALID_AGGREGATIONS, "Invalid AGGREGATION_WINDOW provided"
assert PLAYER_AGGREGATE in VALID_STATS, "Invalid PLAYER_AGGREGATE provided"

assert MAX_RATIO == 1.0, "MAX_RATIO must be 1.0"
assert MIN_RATIO > 0.0 and MIN_RATIO < 1.0, "MIN_RATIO must be between 0.0 and 1.0"
assert RATIO_STEP in [0.01, 0.02, 0.05, 0.1], "Invalid RATIO_STEP provided"

assert not set(AVG_MEDAL_CUMULATIVE_COUNTS.keys()) - {'gold', 'silver', 'bronze'}, \
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

dates_to_show = get_aggregation_dates(daily_ratings, agg_window = AGGREGATION_WINDOW, \
                                      start_date = START_DATE, end_date = END_DATE)
date_to_agg_date = date_to_aggregation_date(daily_ratings.keys(), dates_to_show)

aggregate_ratings = get_aggregate_ratings(daily_ratings, agg_dates = dates_to_show, \
                                          date_to_agg_date = date_to_agg_date, \
                                          player_aggregate = PLAYER_AGGREGATE)

for i, d in enumerate(dates_to_show):
  if d.year in SKIP_YEARS:
    del dates_to_show[i]
if dates_to_show[-1] == END_DATE:
  dates_to_show.pop()


def get_aggregate_ratios(aggregate_ratings):
  aggregate_ratios = {}
  for d in aggregate_ratings:
    aggregate_ratios[d] = {}
    max_rating = max(aggregate_ratings[d].values())
    for p in aggregate_ratings[d]:
      rating = aggregate_ratings[d][p]
      if rating >= THRESHOLD:
        aggregate_ratios[d][p] = rating / max_rating
  return aggregate_ratios

aggregate_ratings = get_aggregate_ratios(aggregate_ratings)

if SHOW_TOP_STATS:
  player_stats = get_player_stats(aggregate_ratings, dates_to_show, \
                                  top_players = TOP_PLAYERS)
  show_top_stats(player_stats, sort_by = TOP_STATS_SORT, \
                  top_players = TOP_PLAYERS, dtype = DTYPE)

if SHOW_TOP_MEDALS or SHOW_GRAPH:
  ratio_stops = np.linspace(MIN_RATIO, MAX_RATIO, RATIO_BINS + 1)
  actual_ratio_stops = ratio_stops[ : -1]

  metrics_bins, player_counts_by_step, player_periods = \
          get_metrics_by_stops(aggregate_ratings, stops = ratio_stops, \
                                dates = dates_to_show, \
                                by_percentage = BY_MEDAL_PERCENTAGES, \
                                show_bin_counts = SHOW_BIN_COUNTS, \
                              )

  reversed_stops = list(reversed(actual_ratio_stops))

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
                        'LABEL_KEY': 'ratio', 'LABEL_TEXT': 'Ratio vs top player', \
                        'DTYPE': DTYPE, \
                        }

  yparams_max = MAX_RATIO
  if TRIM_EMPTY_ROWS:
    for i, s in enumerate(reversed_stops):
      if graph_metrics['lines'][i][1] == 0:
        yparams_max = s
      else:
        break
  if SHOW_MEDALS and TRUNCATE_GRAPH_AT:
    yparams_min = medal_stats[TRUNCATE_GRAPH_AT]['threshold'] - RATIO_STEP
  else:
    yparams_min = MIN_RATIO
  graph_yparams = {'min': yparams_min, 'max': yparams_max, 'step': RATIO_STEP}

  plot_interval_graph(graph_metrics, stops = reversed_stops, \
                      annotations = graph_annotations, yparams = graph_yparams, \
                      medal_stats = medal_stats, show_medals = SHOW_MEDALS)
