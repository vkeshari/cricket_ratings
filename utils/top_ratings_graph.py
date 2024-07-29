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

DTYPE = 'int'

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
RATING_STEP = 10

# ['', 'rating', 'rank', 'either', 'both']
CHANGED_DAYS_CRITERIA = 'rating'

# Aggregation
# See common.aggregation.VALID_AGGREGATIONS for possible windows
AGGREGATION_WINDOW = 'yearly'
# See common.stats.VALID_STATS for possible aggregate stats
PLAYER_AGGREGATE = 'max'

SHOW_BIN_COUNTS = False

SHOW_TOP_STATS = True
TOP_STATS_SORT = ('max', 'avg')

SHOW_TOP_MEDALS = True
BY_MEDAL_PERCENTAGES = False
AVG_MEDAL_CUMULATIVE_COUNTS = [2, 5, 10]
MEDAL_LABELS = ['gold', 'silver', 'bronze']

SHOW_GRAPH = True
TRIM_EMPTY_ROWS = True
SHOW_MEDALS = True
# A value from AVG_MEDAL_CUMULATIVE_COUNTS
TRUNCATE_GRAPH_AT = 10
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
assert RATING_STEP >= 5, "RATING_STEP must be at least 5"

assert CHANGED_DAYS_CRITERIA in ['', 'rating', 'rank', 'either', 'both']

assert AGGREGATION_WINDOW in VALID_AGGREGATIONS, "Invalid AGGREGATION_WINDOW provided"
assert PLAYER_AGGREGATE in VALID_STATS, "Invalid PLAYER_AGGREGATE provided"

for amcc in AVG_MEDAL_CUMULATIVE_COUNTS:
  assert amcc > 0, "All values in AVG_MEDAL_CUMULATIVE_COUNTS must be positive"
assert AVG_MEDAL_CUMULATIVE_COUNTS == sorted(AVG_MEDAL_CUMULATIVE_COUNTS), \
        "AVG_MEDAL_CUMULATIVE_COUNTS must be sorted"
if MEDAL_LABELS:
  assert len(MEDAL_LABELS) == len(AVG_MEDAL_CUMULATIVE_COUNTS), \
        "MEDAL_LABELS and AVG_MEDAL_CUMULATIVE_COUNTS should have the same length"

if SHOW_MEDALS:
  assert SHOW_GRAPH, "SHOW_GRAPH must be enabled if SHOW_MEDALS is enabled"
assert TRUNCATE_GRAPH_AT in AVG_MEDAL_CUMULATIVE_COUNTS, \
        "TRUNCATE_GRAPH_AT larger than AVG_MEDAL_CUMULATIVE_COUNTS"
if TRUNCATE_GRAPH_AT:
  assert SHOW_MEDALS, "SHOW_MEDALS must be enabled if TRUNCATE_GRAPH_AT is set"

if TOP_STATS_SORT:
  assert SHOW_TOP_STATS, "SHOW_TOP_STATS must be enabled if TOP_STATS_SORT is enabled"
  assert not set(TOP_STATS_SORT) - {'span', 'avg', 'max', 'sum'}, \
      "Invalid sort parameter in TOP_STATS_SORT"

assert TOP_PLAYERS > 5, "TOP_PLAYERS must be at least 5"


if MEDAL_LABELS:
  ALL_MEDALS = MEDAL_LABELS
else:
  ALL_MEDALS = ['T' + str(c) for c in AVG_MEDAL_CUMULATIVE_COUNTS]

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
date_to_agg_date = date_to_aggregation_date(dates = list(daily_ratings.keys()), \
                                                    aggregation_dates = dates_to_show)

aggregate_ratings = get_aggregate_ratings(daily_ratings, agg_dates = dates_to_show, \
                                          date_to_agg_date = date_to_agg_date, \
                                          player_aggregate = PLAYER_AGGREGATE)

for i, d in enumerate(dates_to_show):
  if d.year in SKIP_YEARS:
    del dates_to_show[i]
if dates_to_show[-1] == END_DATE:
  dates_to_show.pop()


def filter_by_threshold(aggregate_ratings):
  aggregate_filtered = {}
  for d in aggregate_ratings:
    aggregate_filtered[d] = {}
    for p in aggregate_ratings[d]:
      rating = aggregate_ratings[d][p]
      if rating >= THRESHOLD:
        aggregate_filtered[d][p] = rating
  return aggregate_filtered

aggregate_ratings = filter_by_threshold(aggregate_ratings)

if SHOW_TOP_STATS:
  player_stats = get_player_stats(aggregate_ratings, dates_to_show, \
                                  top_players = TOP_PLAYERS)
  show_top_stats(player_stats, sort_by = TOP_STATS_SORT, \
                  top_players = TOP_PLAYERS, dtype = DTYPE)

if SHOW_TOP_MEDALS or SHOW_GRAPH:
  rating_stops = list(range(THRESHOLD, MAX_RATING, RATING_STEP))
  actual_rating_stops = rating_stops[ : -1]

  metrics_bins, player_counts_by_step, player_periods = \
          get_metrics_by_stops(aggregate_ratings, stops = rating_stops, \
                                dates = dates_to_show, \
                                by_percentage = BY_MEDAL_PERCENTAGES, \
                                show_bin_counts = SHOW_BIN_COUNTS, \
                              )

  reversed_stops = list(reversed(actual_rating_stops))

  graph_metrics = get_graph_metrics(metrics_bins, stops = reversed_stops, \
                                    dates = dates_to_show, \
                                    cumulatives = GRAPH_CUMULATIVES)


  medal_stats = get_medal_stats(graph_metrics, stops = reversed_stops, \
                                all_medals = ALL_MEDALS, \
                                avg_medal_cumulative_counts = AVG_MEDAL_CUMULATIVE_COUNTS)

  player_medals = get_player_medals(player_counts_by_step, medal_stats, \
                                    all_medals = ALL_MEDALS)


if SHOW_TOP_MEDALS:
  show_top_medals(player_medals, player_periods, all_medals = ALL_MEDALS, \
                    top_players = TOP_PLAYERS, by_percentage = BY_MEDAL_PERCENTAGES)

if SHOW_GRAPH:
  graph_annotations = {'TYPE': TYPE, 'FORMAT': FORMAT, \
                        'START_DATE': START_DATE, 'END_DATE': END_DATE, \
                        'AGGREGATION_WINDOW': AGGREGATION_WINDOW, \
                        'AGG_TYPE': PLAYER_AGGREGATE, 'AGG_LOCATION': 'y', \
                        'LABEL_METRIC': 'No. of Players', \
                        'LABEL_KEY': 'rating', 'LABEL_TEXT': 'Rating', \
                        'DTYPE': DTYPE, \
                        }

  yparams_max = MAX_RATING
  if TRIM_EMPTY_ROWS:
    for i, s in enumerate(reversed_stops):
      if graph_metrics['lines'][i][1] == 0:
        yparams_max = s
      else:
        break
  if SHOW_MEDALS and TRUNCATE_GRAPH_AT:
    truncation_medal_index = AVG_MEDAL_CUMULATIVE_COUNTS.index(TRUNCATE_GRAPH_AT)
    truncation_medal = ALL_MEDALS[truncation_medal_index]
    yparams_min = medal_stats[truncation_medal]['threshold'] - RATING_STEP
  else:
    yparams_min = THRESHOLD
  graph_yparams = {'min': yparams_min, 'max': yparams_max, 'step': RATING_STEP}

  plot_interval_graph(graph_metrics, stops = reversed_stops, \
                      annotations = graph_annotations, yparams = graph_yparams, \
                      medal_stats = medal_stats, show_medals = SHOW_MEDALS)
