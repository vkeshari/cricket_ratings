from common.aggregation import aggregate_values, is_aggregation_window_start, \
                                get_aggregate_ratings, get_metrics_by_stops
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
RATING_STEP = 20

# ['', 'rating', 'rank', 'either', 'both']
CHANGED_DAYS_CRITERIA = 'rating'

# Aggregation
# ['', 'monthly', 'quarterly', 'halfyearly', 'yearly', 'decadal']
AGGREGATION_WINDOW = 'yearly'
# ['', 'avg', 'median', 'min', 'max', 'first', 'last']
PLAYER_AGGREGATE = 'max'

GRAPH_CUMULATIVES = True

AVG_MEDAL_CUMULATIVE_COUNTS = {'gold': 2, 'silver': 5, 'bronze': 10}

SHOW_BIN_COUNTS = False
SHOW_GRAPH = True
SHOW_MEDALS = True
TRUNCATE_AT_BRONZE = True

SHOW_TOP_PLAYERS = True
TOP_PLAYERS = 25
BY_MEDAL_PERCENTAGES = False

# Alternate way to calculate allrounder ratings. Use geometric mean of batting and bowling.
ALLROUNDERS_GEOM_MEAN = True

assert TYPE in ['batting', 'bowling', 'allrounder'], "Invalid TYPE provided"
assert FORMAT in ['test', 'odi', 't20'], "Invalid FORMAT provided"
assert START_DATE < END_DATE, "START_DATE must be earlier than END_DATE"
assert END_DATE <= date.today(), "Future END_DATE requested"

assert MAX_RATING <= 1000, "MAX_RATING must not be greater than 1000"
assert THRESHOLD >= 0 and THRESHOLD < MAX_RATING, \
      "THRESHOLD must be between 0 and MAX_RATING"
assert RATING_STEP >= 10, "RATING_STEP must be at least 10"

assert CHANGED_DAYS_CRITERIA in ['', 'rating', 'rank', 'either', 'both']

assert AGGREGATION_WINDOW in ['monthly', 'quarterly', 'halfyearly', 'yearly', 'decadal'], \
      "Invalid AGGREGATION_WINDOW provided"
assert PLAYER_AGGREGATE in ['avg', 'median', 'min', 'max', 'first', 'last'], \
      "Invalid PLAYER_AGGREGATE provided"

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
                        'LABEL_KEY': 'rating', 'LABEL_TEXT': 'Rating', \
                        'DTYPE': 'int', \
                        }

  if SHOW_MEDALS and TRUNCATE_AT_BRONZE:
    yparams_min = medal_stats['bronze']['threshold'] - RATING_STEP
  else:
    yparams_min = THRESHOLD
  graph_yparams = {'min': yparams_min, 'max': MAX_RATING, 'step': RATING_STEP}

  plot_interval_graph(graph_metrics, stops = reversed_stops, \
                      annotations = graph_annotations, yparams = graph_yparams, \
                      medal_stats = medal_stats, show_medals = SHOW_MEDALS)
