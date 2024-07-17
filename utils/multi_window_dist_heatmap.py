from common.aggregation import is_aggregation_window_start, \
                                get_next_aggregation_window_start, \
                                get_aggregated_distribution, VALID_AGGREGATIONS
from common.data import get_daily_ratings
from common.output import pretty_format, get_type_color, resolution_by_span, \
                          get_timescale_xticks
from common.stats import fit_exp_curve, normalize_array, VALID_STATS

from datetime import date
from matplotlib import pyplot as plt, animation
from pathlib import Path

import numpy as np
import math

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


def process_for_day(graph_date, daily_ratings):

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

  if PLOT_PERCENTILES:
    stats_bin_size = (MAX_RATING - THRESHOLD) / 100
    stats_bin_stops = np.linspace(THRESHOLD, MAX_RATING, 101)
    stats_buckets, stats_bins = get_aggregated_distribution(daily_ratings, \
                                    agg_dates = [graph_date], \
                                    date_to_agg_date = date_to_agg_date, \
                                    dist_aggregate = BIN_AGGREGATE, \
                                    bin_stops = stats_bin_stops)

    stats_bin_counts = normalize_array(stats_buckets[graph_date])
    stats_bins = stats_bins[ : -1]

  all_percentiles = {}
  if PLOT_PERCENTILES:
    for p in PLOT_PERCENTILES:
      cum_sum = 0
      for i, b in enumerate(stats_bins):
        cum_sum += stats_bin_counts[i]
        if cum_sum >= p:
          all_percentiles[p] = b
          break

  return bin_counts, all_percentiles


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
    bin_counts, percentiles = process_for_day(graph_date, daily_ratings)
    all_bin_counts[graph_date] = bin_counts
    all_percentiles[graph_date] = percentiles

  adjusted_start_date = GRAPH_DATES[0]
  adjusted_end_date = date(GRAPH_DATES[-1].year + 1, 1 ,1)

  resolution, aspect_ratio = resolution_by_span(adjusted_start_date, adjusted_end_date, \
                                                heatmap = True)
  fig, ax = plt.subplots(figsize = resolution)

  title_text = "Heatmap of Distribution of Ratings by Year" \
                + "\n" + pretty_format(frmt, typ) + ": "\
                + str(adjusted_start_date) + " to " + str(adjusted_end_date) \
                + ' (' + AGGREGATION_WINDOW + ' ' + BIN_AGGREGATE + ')'
  ax.set_title(title_text, fontsize ='x-large')

  ax.set_ylabel('No. of players (normalized to 100)', fontsize ='x-large')

  ax.set_ylabel('Rating', fontsize ='x-large')
  ax.set_ylim(THRESHOLD, MAX_RATING)
  possible_yticks_major = range(0, 1000, 100)
  possible_yticks_minor = range(0, 1000, 20)
  yticks_major = [r for r in possible_yticks_major if r >= THRESHOLD and r <= MAX_RATING]
  yticks_minor= [r for r in possible_yticks_minor if r >= THRESHOLD and r <= MAX_RATING]
  ax.set_yticks(yticks_major)
  ax.set_yticks(yticks_minor, minor = True)
  ax.set_yticklabels([str(y) for y in yticks_major], fontsize ='large')

  xticks_major, xticks_minor, xticklabels = \
          get_timescale_xticks(adjusted_start_date, adjusted_end_date, \
                                format = aspect_ratio)
  ax.set_xticks(xticks_major)
  ax.set_xticks(xticks_minor, minor = True)
  ax.set_xticklabels(xticklabels, fontsize ='large')

  ax.grid(True, which = 'major', axis = 'both', alpha = 0.6)
  ax.grid(True, which = 'minor', axis = 'both', alpha = 0.3)

  heatmap_changes = np.array(list(zip(*all_bin_counts.values())))
  if LOG_SCALE:
    for i, hc in enumerate(heatmap_changes):
      log_vals = [np.log10(v) if v > 0 else -1.5 for v in hc]
      heatmap_changes[i] = log_vals

  plt.imshow(heatmap_changes, origin = 'lower', aspect = 'auto', \
                extent = (adjusted_start_date, adjusted_end_date, \
                            THRESHOLD, MAX_RATING))


  if LOG_SCALE:
    cbar_ticks = np.linspace(0, 3, 7)
    cbar_ticklabels = [str(int(math.pow(10, t))) for t in cbar_ticks]
  else:
    cbar_ticks = range(0, 100, 10)
    cbar_ticklabels = [str(t) for t in cbar_ticks]
  cbar = plt.colorbar(ticks = cbar_ticks, aspect = 25)
  cbar.ax.set_yticklabels(cbar_ticklabels, fontsize = 'medium')
  if LOG_SCALE:
    cbar.set_label(label = 'Interval Frequency (log scale)', size = 'x-large')
  else:
    cbar.set_label(label = 'Interval Frequency', size = 'x-large')
  cbar.ax.tick_params(labelsize = 'medium')

  fig.tight_layout()

  out_filename = 'out/images/heatmap/distagg/' + str(THRESHOLD) + '_' \
                  + str(MAX_RATING) + '_' + str(BIN_SIZE) + '_' \
                  + ('LOG_' if LOG_SCALE else '') \
                  + AGGREGATION_WINDOW + '_' + BIN_AGGREGATE + '_' \
                  + frmt + '_' + typ + '_' \
                  + str(adjusted_start_date.year) + '_' \
                  + str(adjusted_end_date.year) + '.png'

  Path(out_filename).parent.mkdir(exist_ok = True, parents = True)
  fig.savefig(out_filename)
  print("Written: " + out_filename)

