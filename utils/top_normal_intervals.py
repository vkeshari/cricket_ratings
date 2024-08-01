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
AVG_MEDAL_CUMULATIVE_COUNTS = [2, 5, 10]
MEDAL_LABELS = ['gold', 'silver', 'bronze']

TOP_PLAYERS = 25

SHOW_GRAPH = True
TRIM_EMPTY_ROWS = True
SHOW_MEDALS = True
GRAPH_CUMULATIVES = True
# A value from AVG_MEDAL_CUMULATIVE_COUNTS
TRUNCATE_GRAPH_AT = 10

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

assert MAX_SIGMA >= 1.0, "MAX_SIGMA must greater than 1.0"
assert MIN_SIGMA >= 0.0 and MIN_SIGMA < MAX_SIGMA, \
      "MIN_SIGMA must be between 0.0 and MAX_SIGMA"
assert SIGMA_STEP in [0.05, 0.1, 0.2, 0.5], "Invalid SIGMA_STEP provided"

for amcc in AVG_MEDAL_CUMULATIVE_COUNTS:
  assert amcc > 0, "All values in AVG_MEDAL_CUMULATIVE_COUNTS must be positive"
assert AVG_MEDAL_CUMULATIVE_COUNTS == sorted(AVG_MEDAL_CUMULATIVE_COUNTS), \
        "AVG_MEDAL_CUMULATIVE_COUNTS must be sorted"
if MEDAL_LABELS:
  assert len(MEDAL_LABELS) == len(AVG_MEDAL_CUMULATIVE_COUNTS), \
        "MEDAL_LABELS and AVG_MEDAL_CUMULATIVE_COUNTS should have the same length"

if SHOW_GRAPH:
  if TRUNCATE_GRAPH_AT:
    assert SHOW_MEDALS, "SHOW_MEDALS must be enabled if TRUNCATE_GRAPH_AT is set"
    assert TRUNCATE_GRAPH_AT in AVG_MEDAL_CUMULATIVE_COUNTS, \
            "TRUNCATE_GRAPH_AT larger than AVG_MEDAL_CUMULATIVE_COUNTS"

if SHOW_TOP_STATS:            
  if TOP_STATS_SORT:
    assert not set(TOP_STATS_SORT) - {'span', 'avg', 'max', 'sum'}, \
        "Invalid sort parameter in TOP_STATS_SORT"

assert TOP_PLAYERS > 5, "TOP_PLAYERS must be at least 5"


if FORMAT == 'test':
  SKIP_YEARS = list(range(1915, 1920)) + list(range(1940, 1946)) + [1970]
elif FORMAT == 'odi':
  SKIP_YEARS = [2018]
elif FORMAT == 't20':
  SKIP_YEARS = [2011]

MEDAL_COUNT = len(AVG_MEDAL_CUMULATIVE_COUNTS)
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

dates_to_show = list(filter(lambda d: d.year not in SKIP_YEARS, dates_to_show))
if dates_to_show[-1] == END_DATE:
  dates_to_show.pop()


def get_normalized_ratings(aggregate_ratings, dates_to_show):
  normalized_ratings = {}

  for d in dates_to_show:
    day_ratings = aggregate_ratings[d]
    day_ratings = {p: (r - THRESHOLD) / (MAX_RATING - THRESHOLD) \
                              for (p, r) in day_ratings.items() if r >= THRESHOLD}
    day_ratings = dict(sorted(day_ratings.items(), \
                              key = lambda item: item[1], reverse = True))

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
                                show_bin_counts = SHOW_BIN_COUNTS)

  reversed_stops = list(reversed(actual_sigma_stops))

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
  title_text = "No. of Players Above Gaussian Std Devs"
  ylabel = "Gaussian Std Dev"
  xlabel = "No. of Players above std dev"
  graph_annotations = {'TYPE': TYPE, 'FORMAT': FORMAT, \
                        'START_DATE': START_DATE, 'END_DATE': END_DATE, \
                        'AGGREGATION_WINDOW': AGGREGATION_WINDOW, \
                        'AGG_TYPE': PLAYER_AGGREGATE, 'AGG_LOCATION': 'y', \
                        'TITLE': title_text, 'YLABEL': ylabel, 'XLABEL': xlabel, \
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
    truncation_medal_index = AVG_MEDAL_CUMULATIVE_COUNTS.index(TRUNCATE_GRAPH_AT)
    truncation_medal = ALL_MEDALS[truncation_medal_index]
    yparams_min = medal_stats[truncation_medal]['threshold'] - SIGMA_STEP
  else:
    yparams_min = MIN_SIGMA
  graph_yparams = {'min': yparams_min, 'max': yparams_max, 'step': SIGMA_STEP}

  out_filename = 'out/images/interval/topplayers/normal/' \
                    + str(MIN_SIGMA) + '_' + str(MAX_SIGMA) + '_' \
                    + str(SIGMA_STEP) + '_' \
                    + (str(MEDAL_COUNT) + 'MEDALS_' \
                              if SHOW_TOP_MEDALS and MEDAL_COUNT else '') \
                    + AGGREGATION_WINDOW + '_' + PLAYER_AGGREGATE + '_' \
                    + FORMAT + '_' + TYPE \
                    + ('GEOM' if TYPE == 'allrounder' and ALLROUNDERS_GEOM_MEAN else '') \
                    + '_' + str(START_DATE.year) + '_' + str(END_DATE.year) + '.png'

  plot_interval_graph(graph_metrics, stops = reversed_stops, \
                      annotations = graph_annotations, yparams = graph_yparams, \
                      medal_stats = medal_stats, show_medals = SHOW_MEDALS, \
                      save_filename = out_filename)
