from common.aggregation import is_aggregation_window_start, \
                                get_next_aggregation_window_start, \
                                get_aggregated_distribution
from common.data import get_daily_ratings
from common.output import get_colors_from_scale
from common.stats import get_stats_for_list, normalize_array

from datetime import date
from matplotlib import pyplot as plt
from pathlib import Path

import numpy as np
import math

# ['', 'batting', 'bowling', 'allrounder']
TYPE = 'bowling'
# ['', 'test', 'odi', 't20']
FORMAT = 'test'

# Graph dates
START_DATE = date(1948, 1, 1)
END_DATE = date(1993, 1, 1)

GRAPH_DATES = [date(y, 1, 1) for y in range(START_DATE.year, END_DATE.year)]

# Upper and lower bounds of ratings to show
THRESHOLD = 0
MAX_RATING = 1000

# ['', 'monthly', 'quarterly', 'halfyearly', 'yearly', 'decadal']
AGGREGATION_WINDOW = 'yearly'
# ['', 'avg', 'median', 'min', 'max', 'first', 'last']
BIN_AGGREGATE = 'avg'

# ['', 'rating', 'rank', 'either', 'both']
CHANGED_DAYS_CRITERIA = 'rating'

SHOW_BIN_COUNTS = False
SHOW_GRAPH = True
PLOT_RATINGS = [100, 250, 500]
PERCENTILE_BIN_SIZE = 5
STD = 1

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

assert THRESHOLD == 0 and MAX_RATING == 1000, \
    "Ratings range must be 0 to 1000"

assert CHANGED_DAYS_CRITERIA in ['', 'rating', 'rank', 'either', 'both']

assert AGGREGATION_WINDOW in ['monthly', 'quarterly', 'halfyearly', 'yearly', 'decadal'], \
      "Invalid AGGREGATION_WINDOW provided"
assert BIN_AGGREGATE in ['avg', 'median', 'min', 'max', 'first', 'last'], \
      "Invalid BIN_AGGREGATE provided"

assert PLOT_RATINGS
for r in PLOT_RATINGS:
  assert r > THRESHOLD and r < MAX_RATING, \
    "Each value in PLOT_RATINGS must be between THRESHOLD and MAX_RATING"

assert PERCENTILE_BIN_SIZE >= 1 and PERCENTILE_BIN_SIZE <= 10, \
    "PERCENTILE_BIN_SIZE should be between 1 and 10"
assert 100 % PERCENTILE_BIN_SIZE == 0, "PERCENTILE_BIN_SIZE should be a factor of 100"

assert STD > 0 and STD <= 3, "STD must be between 0 and 3"

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

  ratings_by_window = {r: [] for r in PLOT_RATINGS}

  for graph_date in GRAPH_DATES:
    next_d = get_next_aggregation_window_start(graph_date, AGGREGATION_WINDOW)

    date_to_agg_date = {d: graph_date for d in daily_ratings \
                                if d >= graph_date and d < next_d}

    stats_bin_size = (MAX_RATING - THRESHOLD) / 100
    stats_bin_stops = np.linspace(THRESHOLD, MAX_RATING, 101)
    stats_buckets, stats_bins = get_aggregated_distribution(daily_ratings, \
                                    agg_dates = [graph_date], \
                                    date_to_agg_date = date_to_agg_date, \
                                    dist_aggregate = BIN_AGGREGATE, \
                                    bin_stops = stats_bin_stops)

    stats_bin_counts = normalize_array(stats_buckets[graph_date])
    actual_stats_bins = stats_bins[ : -1]

    for r in PLOT_RATINGS:
      cum_sum = 0
      for i, b in enumerate(actual_stats_bins):
        cum_sum += stats_bin_counts[i]
        if b == r or b < r and actual_stats_bins[i + 1] > r:
          ratings_by_window[r].append(cum_sum)
          break

  print ("Rating percentiles data built for " + str(len(ratings_by_window)) + " years")


  if SHOW_GRAPH:
    resolution = tuple([7.2, 7.2])
    fig, ax = plt.subplots(figsize = resolution)

    title_text = "Distribution of " + frmt + " " + typ \
                  + " ratings by percentile\n" \
                  + str(START_DATE) + ' to ' + str(END_DATE) \
                  + ' (' + AGGREGATION_WINDOW + ' ' + BIN_AGGREGATE + ')'
    ax.set_title(title_text, fontsize ='xx-large')

    ax.set_ylabel('No. of years', fontsize ='x-large')
    ymax = PERCENTILE_BIN_SIZE * 5
    ax.set_ylim(0, ymax)
    if ymax < 30:
      ytick_size = 1
    else:
      ytick_size = 2
    yticks = range(0, ymax + 1, ytick_size)
    ax.set_yticks(yticks)
    ax.set_yticklabels([str(y) for y in yticks], fontsize ='large')

    ax.set_xlabel('Percentile', fontsize ='x-large')
    ax.set_xlim(0, 100)
    xticks = range(0, 101, 10)
    ax.set_xticks(xticks)
    ax.set_xticklabels([str(x) for x in xticks], fontsize ='large')

    ax.grid(True, which = 'both', axis = 'both', alpha = 0.5)

    graph_bins = range(0, 101, PERCENTILE_BIN_SIZE)

    colors = get_colors_from_scale(len(ratings_by_window.keys()))
    for i, r in enumerate(ratings_by_window.keys()):
      ax.hist(ratings_by_window[r], bins = graph_bins, align = 'mid', \
                  label = '{r:3d}'.format(r = r), color = colors[i], alpha = 0.5)
      rating_avg = get_stats_for_list(ratings_by_window[r], 'avg')
      rating_std = get_stats_for_list(ratings_by_window[r], 'std')
      rating_yloc = 0.95 - i * 0.05
      plt.axvline(x = rating_avg, ymax = rating_yloc, linewidth = 3, \
                    color = colors[i], alpha = 1.0, linestyle = ':')

      r_text = str(r) + ': ' \
                + '{a:2.0f}p +/- {s:2.0f}'.format(a = rating_avg, s = STD * rating_std)
      plt.text(x = rating_avg - 1, y = ymax * rating_yloc, \
                s = r_text, alpha = 0.8, fontsize = 'large', color = 'black', \
                horizontalalignment = 'right', verticalalignment = 'center')

    ax.legend(loc = 'best', fontsize = 'large')

    fig.tight_layout()

    out_filename = 'out/images/hist/ratings/' + str(THRESHOLD) + '_' \
                    + str(MAX_RATING) + '_' + str(PERCENTILE_BIN_SIZE) + '_' \
                    + str(STD) + 'std_' \
                    + AGGREGATION_WINDOW + '_' + BIN_AGGREGATE + '_' \
                    + frmt + '_' + typ + '_' \
                    + str(START_DATE.year) + '_' + str(END_DATE.year) + '.png'

    Path(out_filename).parent.mkdir(exist_ok = True, parents = True)
    fig.savefig(out_filename)
    print("Written: " + out_filename)
