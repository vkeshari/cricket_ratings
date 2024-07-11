from common.aggregation import is_aggregation_window_start, \
                                get_next_aggregation_window_start, \
                                get_aggregated_distribution
from common.data import get_daily_ratings
from common.stats import fit_dist_to_hist, normalize_array

from datetime import date
from fitter import Fitter
from matplotlib import pyplot as plt
from pathlib import Path

import numpy as np
import math

# ['', 'batting', 'bowling', 'allrounder']
TYPE = 'batting'
# ['', 'test', 'odi', 't20']
FORMAT = 'test'

# Graph dates
GRAPH_DATES = [date(1930, 1, 1)]

# Upper and lower bounds of ratings to show
THRESHOLD = 0
MAX_RATING = 1000
BIN_SIZE = 50

# ['', 'monthly', 'quarterly', 'halfyearly', 'yearly', 'decadal']
AGGREGATION_WINDOW = 'decadal'
# ['', 'avg', 'median', 'min', 'max', 'first', 'last']
BIN_AGGREGATE = 'avg'

# ['', 'rating', 'rank', 'either', 'both']
CHANGED_DAYS_CRITERIA = 'rating'

SHOW_BIN_COUNTS = False

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

assert AGGREGATION_WINDOW in ['monthly', 'quarterly', 'halfyearly', 'yearly', 'decadal'], \
      "Invalid AGGREGATION_WINDOW provided"
assert BIN_AGGREGATE in ['avg', 'median', 'min', 'max', 'first', 'last'], \
      "Invalid BIN_AGGREGATE provided"

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

  first_date = min(daily_ratings.keys())
  last_date = max(daily_ratings.keys())

  for graph_date in GRAPH_DATES:
    print (graph_date)

    next_d = get_next_aggregation_window_start(graph_date, AGGREGATION_WINDOW)

    date_to_agg_date = {d: graph_date for d in daily_ratings \
                                if d >= graph_date and d < next_d}
    bin_stops = list(range(THRESHOLD, MAX_RATING, BIN_SIZE)) + [MAX_RATING]

    aggregated_buckets, bins = get_aggregated_distribution(daily_ratings, \
                                      agg_dates = [graph_date], \
                                      date_to_agg_date = date_to_agg_date, \
                                      dist_aggregate = BIN_AGGREGATE, \
                                      bin_stops = bin_stops)

    bin_counts = normalize_array(aggregated_buckets[graph_date])
    actual_bins = bins[ : -1]


    if SHOW_BIN_COUNTS:
      print("=== " + AGGREGATION_WINDOW + " " + BIN_AGGREGATE \
            + " bin counts (" + frmt + " " + typ + ") on " + str(graph_date) + " ===")
      print("BIN\tCOUNT")

      for i, b in enumerate(actual_bins):
        print ('{b:3d}\t{bc:5.2f}'.format(b = b, bc = bin_counts[i]))
      print ("TOTAL:\t{t:5.2f}".format(t = sum(bin_counts)))

    dist_fit = fit_dist_to_hist(bin_counts, actual_bins, bin_width = BIN_SIZE, \
                                range = (THRESHOLD, MAX_RATING), scale_bins = 100)
