from common.aggregation import is_aggregation_window_start, VALID_AGGREGATIONS, \
                                get_single_window_distribution
from common.data import get_daily_ratings
from common.dist_heatmap import plot_dist_heatmap
from common.stats import VALID_STATS

from datetime import date
from matplotlib import pyplot as plt
from pathlib import Path

# ['', 'batting', 'bowling', 'allrounder']
TYPE = ''
# ['', 'test', 'odi', 't20']
FORMAT = 't20'

# Graph dates
GRAPH_DATES = [date(y, 1, 1) for y in range(2007, 2024)]

# Upper and lower bounds of ratings to show
THRESHOLD = 500
MAX_RATING = 1000
BIN_SIZE = 10

# See common.aggregation.VALID_AGGREGATIONS for possible windows
AGGREGATION_WINDOW = 'yearly'
# See common.stats.VALID_STATS for possible aggregate stats
BIN_AGGREGATE = 'avg'

# ['', 'rating', 'rank', 'either', 'both']
CHANGED_DAYS_CRITERIA = 'rating'

LOG_SCALE = True
PLOT_PERCENTILES = []
RESCALE = False

# Alternate way to calculate allrounder ratings. Use geometric mean of batting and bowling.
ALLROUNDERS_GEOM_MEAN = True

if TYPE:
  assert TYPE in ['batting', 'bowling', 'allrounder'], "Invalid TYPE provided"
if FORMAT:
  assert FORMAT in ['test', 'odi', 't20'], "Invalid FORMAT provided"
assert GRAPH_DATES, "GRAPH_DATES is empty"
for gd in GRAPH_DATES:
  assert is_aggregation_window_start(gd, AGGREGATION_WINDOW), \
      "Invalid " + AGGREGATION_WINDOW + " aggregation start date: " + str(gd)

assert MAX_RATING <= 1000, "MAX_RATING must not be greater than 1000"
assert THRESHOLD >= 0 and THRESHOLD < MAX_RATING, \
      "THRESHOLD must be between 0 and MAX_RATING"
assert (MAX_RATING - THRESHOLD) % 100 == 0, "Range of ratings must be a multiple of 100"

assert CHANGED_DAYS_CRITERIA in ['', 'rating', 'rank', 'either', 'both']

assert BIN_SIZE >= 10 and BIN_SIZE <= 100, "BIN_SIZE should be between 10 and 100"
assert (MAX_RATING - THRESHOLD) % BIN_SIZE == 0, \
      "BIN_SIZE should be a factor of ratings range"

assert AGGREGATION_WINDOW in VALID_AGGREGATIONS, "Invalid AGGREGATION_WINDOW provided"
assert BIN_AGGREGATE in VALID_STATS, "Invalid BIN_AGGREGATE provided"

for p in PLOT_PERCENTILES:
  assert p >= 0 and p < 100, "Each value in PLOT_PERCENTILES must be between 0 and 100"


types_and_formats = []
if TYPE and FORMAT:
  types_and_formats.append((TYPE, FORMAT))
elif TYPE:
  for f in ['test', 'odi', 't20']:
    types_and_formats.append((TYPE, f))
elif FORMAT:
  for t in ['batting', 'bowling']:
    types_and_formats.append((t, FORMAT))
else:
  for f in ['test', 'odi', 't20']:
    for t in ['batting', 'bowling']:
      types_and_formats.append((t, f))

for typ, frmt in types_and_formats:
  print (frmt + ' : ' + typ)
  print (str(THRESHOLD) + ' : ' + str(BIN_SIZE) + ' : ' + str(MAX_RATING))

  daily_ratings, _ = get_daily_ratings(typ, frmt, \
                            changed_days_criteria = CHANGED_DAYS_CRITERIA, \
                            allrounders_geom_mean = ALLROUNDERS_GEOM_MEAN)

  all_bin_counts, all_percentiles = {}, {}
  for graph_date in GRAPH_DATES:
    bin_counts, actual_bins, percentiles, _, _ = \
            get_single_window_distribution(daily_ratings, agg_date = graph_date, \
                                            agg_window = AGGREGATION_WINDOW, \
                                            agg_type = BIN_AGGREGATE, \
                                            threshold = THRESHOLD, \
                                            max_rating = MAX_RATING, \
                                            bin_size = BIN_SIZE, \
                                            get_percentiles = PLOT_PERCENTILES, \
                                            rescale = RESCALE)

    all_bin_counts[graph_date] = bin_counts
    all_percentiles[graph_date] = percentiles

  plot_dist_heatmap(GRAPH_DATES, all_bin_counts, all_percentiles, \
                    frmt, typ, agg_window = AGGREGATION_WINDOW, agg_type = BIN_AGGREGATE, \
                    agg_title = str(AGGREGATION_WINDOW).title(), \
                    threshold = THRESHOLD, max_rating = MAX_RATING, bin_size = BIN_SIZE, \
                    plot_percentiles = len(PLOT_PERCENTILES) > 0, log_scale = LOG_SCALE, \
                    rescale = RESCALE, allrounders_geom_mean = ALLROUNDERS_GEOM_MEAN)
