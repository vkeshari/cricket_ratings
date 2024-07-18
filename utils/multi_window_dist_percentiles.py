from common.aggregation import is_aggregation_window_start, \
                                get_next_aggregation_window_start, \
                                get_aggregated_distribution, VALID_AGGREGATIONS
from common.data import get_daily_ratings
from common.output import get_colors_from_scale, pretty_format
from common.stats import get_stats_for_list, normalize_array, VALID_STATS

from datetime import date
from matplotlib import pyplot as plt
from pathlib import Path

import numpy as np
import math

# ['', 'batting', 'bowling', 'allrounder']
TYPE = ''
# ['', 'test', 'odi', 't20']
FORMAT = 'test'

# Graph dates
START_DATE = date(1930, 1, 1)
END_DATE = date(1940, 1, 1)

GRAPH_DATES = [date(y, 1, 1) for y in range(START_DATE.year, END_DATE.year)]

# Upper and lower bounds of ratings to show
THRESHOLD = 0
MAX_RATING = 1000
BIN_SIZE = 50

# See common.aggregation.VALID_AGGREGATIONS for possible windows
AGGREGATION_WINDOW = 'yearly'
# See common.stats.VALID_STATS for possible aggregate stats
BIN_AGGREGATE = 'avg'

# ['', 'rating', 'rank', 'either', 'both']
CHANGED_DAYS_CRITERIA = 'rating'

SHOW_BIN_COUNTS = False
SHOW_GRAPH = True
PLOT_PERCENTILES = [50, 75, 90]
RATING_FRACTIONS = False
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

assert MAX_RATING <= 1000, "MAX_RATING must not be greater than 1000"
assert THRESHOLD >= 0 and THRESHOLD < MAX_RATING, \
      "THRESHOLD must be between 0 and MAX_RATING"
assert (MAX_RATING - THRESHOLD) % 100 == 0, "Range of ratings must be a multiple of 100"

assert BIN_SIZE >= 10 and BIN_SIZE <= 100, "BIN_SIZE should be between 10 and 100"
assert (MAX_RATING - THRESHOLD) % BIN_SIZE == 0, \
      "BIN_SIZE should be a factor of ratings range"

assert CHANGED_DAYS_CRITERIA in ['', 'rating', 'rank', 'either', 'both']

assert AGGREGATION_WINDOW in VALID_AGGREGATIONS, "Invalid AGGREGATION_WINDOW provided"
assert BIN_AGGREGATE in VALID_STATS, "Invalid BIN_AGGREGATE provided"

assert PLOT_PERCENTILES
for p in PLOT_PERCENTILES:
  assert p >= 0 and p < 100, "Each value in PLOT_PERCENTILES must be between 0 and 100"
assert RATING_FRACTIONS or THRESHOLD == 0 and MAX_RATING == 1000, \
    "Either RATING_FRACTIONS must be set or ratings range must be 0 to 1000"

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
  print (str(THRESHOLD) + ' : ' + str(BIN_SIZE) + ' : ' + str(MAX_RATING))

  daily_ratings, _ = get_daily_ratings(typ, frmt, \
                            changed_days_criteria = CHANGED_DAYS_CRITERIA, \
                            allrounders_geom_mean = ALLROUNDERS_GEOM_MEAN)

  percentiles_by_window = {p: [] for p in PLOT_PERCENTILES}

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

    for p in PLOT_PERCENTILES:
      cum_sum = 0
      for i, b in enumerate(actual_stats_bins):
        cum_sum += stats_bin_counts[i]
        if cum_sum >= p:
          percentiles_by_window[p].append(b)
          break

  print ("Percentile data built for " + str(len(percentiles_by_window)) + " years")


  if SHOW_GRAPH:
    resolution = tuple([7.2, 7.2])
    fig, ax = plt.subplots(figsize = resolution)

    title_text = "Distribution of " + pretty_format(frmt, typ) \
                  + " Percentiles by Rating\n" \
                  + str(START_DATE) + ' to ' + str(END_DATE) \
                  + ' (' + AGGREGATION_WINDOW + ' ' + BIN_AGGREGATE + ')'
    ax.set_title(title_text, fontsize ='xx-large')

    ax.set_ylabel('No. of years', fontsize ='x-large')
    ymax = max(10, int(BIN_SIZE / 2))
    ax.set_ylim(0, ymax)
    if ymax < 30:
      ytick_size = 1
    else:
      ytick_size = 2
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

    graph_bins = range(THRESHOLD, MAX_RATING + 1, BIN_SIZE)

    colors = get_colors_from_scale(len(percentiles_by_window.keys()))
    for i, p in enumerate(percentiles_by_window.keys()):
      ax.hist(percentiles_by_window[p], bins = graph_bins, align = 'mid', \
                  label = 'p{p:2d}'.format(p = p), color = colors[i], alpha = 0.5)
      percentile_avg = get_stats_for_list(percentiles_by_window[p], 'avg')
      percentile_std = get_stats_for_list(percentiles_by_window[p], 'std')
      percentile_yloc = 0.95 - i * 0.05
      plt.axvline(x = percentile_avg, ymax = percentile_yloc, linewidth = 3, \
                    color = colors[i], alpha = 1.0, linestyle = ':')

      if RATING_FRACTIONS:
        perecntile_avg_fraction = (percentile_avg - THRESHOLD) / (MAX_RATING - THRESHOLD)
        perecntile_std_fraction = percentile_std / (MAX_RATING - THRESHOLD)
        p_text = 'pf' + str(p) + ': ' \
                  + '{a:4.2f} +/- {s:4.2f}'.format(a = perecntile_avg_fraction, \
                                                    s = STD * perecntile_std_fraction)
      else:
        p_text = 'p' + str(p) + ': ' \
                  + '{a:3.0f} +/- {s:3.0f}'.format(a = percentile_avg, \
                                                    s = STD * percentile_std)
      plt.text(x = percentile_avg + 10, y = ymax * percentile_yloc, \
                s = p_text, alpha = 0.8, fontsize = 'large', color = 'black', \
                horizontalalignment = 'left', verticalalignment = 'center')

    ax.legend(loc = 'best', fontsize = 'large')

    fig.tight_layout()

    out_filename = 'out/images/hist/percentiles/' + str(THRESHOLD) + '_' \
                    + str(MAX_RATING) + '_' + str(BIN_SIZE) + '_' + str(STD) + 'std_' \
                    + ('PF_' if PLOT_PERCENTILES and RATING_FRACTIONS else '') \
                    + AGGREGATION_WINDOW + '_' + BIN_AGGREGATE + '_' \
                    + frmt + '_' + typ + '_' \
                    + str(START_DATE.year) + '_' + str(END_DATE.year) + '.png'

    Path(out_filename).parent.mkdir(exist_ok = True, parents = True)
    fig.savefig(out_filename)
    print("Written: " + out_filename)
