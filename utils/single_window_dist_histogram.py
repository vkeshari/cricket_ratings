from common.aggregation import is_aggregation_window_start, \
                                get_next_aggregation_window_start, \
                                get_aggregated_distribution
from common.data import get_daily_ratings
from common.output import get_player_colors, readable_name_and_country

from datetime import date
from matplotlib import pyplot as plt
from pathlib import Path

import numpy as np
import math

# ['', 'batting', 'bowling', 'allrounder']
TYPE = 'batting'
# ['', 'test', 'odi', 't20']
FORMAT = 't20'

# Graph dates
GRAPH_DATES = [date(2021, 1, 1)]

# Upper and lower bounds of ratings to show
THRESHOLD = 500
MAX_RATING = 1000
BIN_SIZE = 50

# ['', 'monthly', 'quarterly', 'halfyearly', 'yearly', 'decadal']
AGGREGATION_WINDOW = 'yearly'
# ['', 'avg', 'median', 'min', 'max', 'first', 'last']
BIN_AGGREGATE = 'avg'

# ['', 'rating', 'rank', 'either', 'both']
CHANGED_DAYS_CRITERIA = 'rating'

SHOW_BIN_COUNTS = False
SHOW_GRAPH = True

# Alternate way to calculate allrounder ratings. Use geometric mean of batting and bowling.
ALLROUNDERS_GEOM_MEAN = True

if TYPE:
  assert TYPE in ['batting', 'bowling', 'allrounder'], "Invalid TYPE provided"
if FORMAT:
  assert FORMAT in ['test', 'odi', 't20'], "Invalid FORMAT provided"
assert GRAPH_DATES, "GRAPH_DATES is empty"

assert MAX_RATING <= 1000, "MAX_RATING must not be greater than 1000"
assert THRESHOLD >= 0 and THRESHOLD < MAX_RATING, \
      "THRESHOLD must be between 0 and MAX_RATING"

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
  print (str(THRESHOLD) + ' : ' + str(MAX_RATING))

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
    bin_counts = aggregated_buckets[graph_date]

    num_players = round(sum(bin_counts))
    actual_bins = bins[ : -1]

    if SHOW_BIN_COUNTS:
      print("=== Bin counts (" + frmt + " " + typ + ") on " + str(graph_date) + " ===")
      print("BIN\tCOUNT")

      for i, b in enumerate(actual_bins):
        print ('{b:3d}\t{bc:3d}'.format(b = b, bc = bin_counts[i]))

    if SHOW_GRAPH:
      resolution = tuple([7.2, 7.2])
      fig, ax = plt.subplots(figsize = resolution)

      title_text = "Distribution of " + frmt + " " + typ \
                    + " players by rating\n" + str(graph_date) \
                    + '(' + AGGREGATION_WINDOW + ' ' + BIN_AGGREGATE + ')'
      ax.set_title(title_text, fontsize ='xx-large')

      ax.set_ylabel('No. of players (normalized)', fontsize ='x-large')
      ymax = math.ceil(max(bin_counts) / 5) * 5
      if ymax <= 20:
        ytick_size = 1
      else:
        ytick_size = 2
      ax.set_ylim(0, ymax)
      yticks = range(0, ymax + 1, ytick_size)
      ax.set_yticks(yticks)
      ax.set_yticklabels([str(y) for y in yticks], fontsize ='large')

      ax.set_xlabel('Rating', fontsize ='x-large')
      ax.set_xlim(THRESHOLD, MAX_RATING)
      possible_xticks = range(0, 1000, 100)
      actual_xticks = [r for r in possible_xticks if r >= THRESHOLD and r <= MAX_RATING]
      ax.set_xticks(actual_xticks)
      ax.set_xticklabels([str(x) for x in actual_xticks], fontsize ='large')

      ax.grid(True, which = 'both', axis = 'both', alpha = 0.5)

      if typ == 'batting':
        graph_color = 'blue'
      elif typ == 'bowling':
        graph_color = 'red'
      ax.bar(actual_bins, bin_counts, width = BIN_SIZE, align = 'edge', \
                color = graph_color, alpha = 0.5)


      plt.text(MAX_RATING - 10, ymax * 0.95, \
                s = 'Total players (normalized): ' + str(num_players), \
                alpha = 1, fontsize = 'x-large', \
                horizontalalignment = 'right', verticalalignment = 'top')

      fig.tight_layout()

      out_filename = 'out/images/hist/distagg/' + str(THRESHOLD) + '_' \
                      + str(MAX_RATING) + '_' + str(BIN_SIZE) + '_' \
                      + AGGREGATION_WINDOW + '_' + BIN_AGGREGATE + '_' \
                      + frmt + '_' + typ + '_' \
                      + str(graph_date.year) + '.png'

      Path(out_filename).parent.mkdir(exist_ok = True, parents = True)
      fig.savefig(out_filename)
      print("Written: " + out_filename)
