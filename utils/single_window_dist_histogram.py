from common.aggregation import is_aggregation_window_start, VALID_AGGREGATIONS, \
                                get_single_window_distribution
from common.data import get_daily_ratings
from common.output import pretty_format, get_type_color
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
RATING_FRACTIONS = True
FIT_CURVE = False
FIXED_YMAX = True
ANIMATE = True

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

if SHOW_BIN_COUNTS:
  assert not ANIMATE, "SHOW_BIN_COUNTS must be disabled if ANIMATE is enabled"

for p in PLOT_PERCENTILES:
  assert p >= 0 and p < 100, "Each value in PLOT_PERCENTILES must be between 0 and 100"
if PLOT_PERCENTILES:
  assert RATING_FRACTIONS or THRESHOLD == 0 and MAX_RATING == 1000, \
      "If PLOT_PERCENTILES is provided, either RATING_FRACTIONS must be set or " \
          + "ratings range must be 0 to 1000"


def get_rating_fraction(r):
  return (r - THRESHOLD) / (MAX_RATING - THRESHOLD)


def process_for_day(graph_date, daily_ratings, fig, ax):
  print (graph_date)

  bin_counts, actual_bins, all_percentiles, (xs_fit, ys_fit, fit_mean) = \
          get_single_window_distribution(daily_ratings, agg_date = graph_date, \
                                          agg_window = AGGREGATION_WINDOW, \
                                          agg_type = BIN_AGGREGATE, \
                                          threshold = THRESHOLD, max_rating = MAX_RATING, \
                                          bin_size = BIN_SIZE, \
                                          get_percentiles = PLOT_PERCENTILES, \
                                          fit_curve = FIT_CURVE)


  if SHOW_BIN_COUNTS:
    print("=== " + AGGREGATION_WINDOW + " " + BIN_AGGREGATE \
          + " bin counts (" + frmt + " " + typ + ") on " + str(graph_date) + " ===")
    print("BIN\tCOUNT")

    for i, b in enumerate(actual_bins):
      print ('{b:3d}\t{bc:5.2f}'.format(b = b, bc = bin_counts[i]))
    print ("TOTAL:\t{t:5.2f}".format(t = sum(bin_counts)))

  if SHOW_GRAPH:
    title_text = "Distribution of " + pretty_format(frmt, typ) \
                  + " by Rating " \
                  + ("(GM)" if ALLROUNDERS_GEOM_MEAN and typ == 'allrounder' else '') \
                  + "\n" + str(graph_date) \
                  + '(' + AGGREGATION_WINDOW + ' ' + BIN_AGGREGATE + ')'
    ax.set_title(title_text, fontsize ='xx-large')

    ax.set_ylabel('No. of players (normalized to 100)', fontsize ='x-large')

    if FIXED_YMAX:
      ymax = max(10, int(BIN_SIZE * 500 / (MAX_RATING - THRESHOLD) ))
    else:
      ymax = math.ceil(max(bin_counts) / 5) * 5
    ax.set_ylim(0, ymax)

    if ymax <= 20:
      ytick_size = 1
    elif ymax <= 50:
      ytick_size = 2
    else:
      ytick_size = 5

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

    ax.bar(actual_bins, bin_counts, width = BIN_SIZE, align = 'edge', \
              color = get_type_color(typ), alpha = 0.5, label = 'Player Counts')

    for i, p in enumerate(all_percentiles):
      p_val = all_percentiles[p]
      if RATING_FRACTIONS:
        p_text = 'pf' + str(p) + ': ' \
                  + '{v:4.2f}'.format(v = get_rating_fraction(p_val))
      else:
        p_text = 'p' + str(p) + ': ' + '{v:3.0f}'.format(v = p_val)
      y_ratio = 0.9 - 0.05 * i

      plt.axvline(x = p_val, ymax = y_ratio, \
                  linestyle = ':', color = 'black', alpha = 0.8)
      plt.text(p_val + 5, y_ratio * ymax, \
                s = p_text, color = 'black', alpha = 0.9, fontsize = 'large', \
                horizontalalignment = 'left', verticalalignment = 'center')

    if fit_mean > 0:
      plt.plot(xs_fit, ys_fit, linewidth = 3, \
                color = 'darkgreen', alpha = 0.5, antialiased = True, \
                label = 'Exponential Fit')
      plt.axvline(x = fit_mean, linestyle = '--', color = 'darkgreen', alpha = 0.5)
      if RATING_FRACTIONS:
        fit_mean_text = '{v:4.2f}'.format(v = get_rating_fraction(fit_mean))
      else:
        fit_mean_text = str(fit_mean)
      plt.text(fit_mean - 5, 0.95 * ymax, s = 'Exp mean: ' + fit_mean_text, \
                color = 'darkgreen', alpha = 0.9, fontsize = 'large', \
                horizontalalignment = 'right', verticalalignment = 'center')

    ax.legend(loc = 'best', fontsize = 'large')


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

  resolution = tuple([7.2, 7.2])
  fig, ax = plt.subplots(figsize = resolution)

  if ANIMATE:
    out_filename = 'out/images/hist/distagg/ANIMATE_' + str(THRESHOLD) + '_' \
                    + str(MAX_RATING) + '_' + str(BIN_SIZE) + '_' \
                    + ('PF_' if PLOT_PERCENTILES and RATING_FRACTIONS else '') \
                    + ('FIT_' if FIT_CURVE else '') \
                    + AGGREGATION_WINDOW + '_' + BIN_AGGREGATE + '_' \
                    + frmt + '_' + typ \
                    + ('GEOM' if typ == 'allrounder' \
                              and ALLROUNDERS_GEOM_MEAN else '') \
                    + '_' + str(GRAPH_DATES[0].year) + '_' + str(GRAPH_DATES[-1].year) \
                    + '.gif'

    writer = animation.FFMpegWriter(fps = 2, bitrate = 5000)
    with writer.saving(fig, out_filename, dpi = 100):
      for graph_date in GRAPH_DATES:
        ax.clear()

        process_for_day(graph_date, daily_ratings, fig, ax)

        plt.draw()
        writer.grab_frame()

    print("Written: " + out_filename)

  else:
    for graph_date in GRAPH_DATES:
      out_filename = 'out/images/hist/distagg/' + str(THRESHOLD) + '_' \
                      + str(MAX_RATING) + '_' + str(BIN_SIZE) + '_' \
                      + ('PF_' if PLOT_PERCENTILES and RATING_FRACTIONS else '') \
                      + ('FIT_' if FIT_CURVE else '') \
                      + AGGREGATION_WINDOW + '_' + BIN_AGGREGATE + '_' \
                      + frmt + '_' + typ \
                      + ('GEOM' if typ == 'allrounder' \
                                and ALLROUNDERS_GEOM_MEAN else '') \
                      + '_' + str(graph_date.year) + '.png'

      process_for_day(graph_date, daily_ratings, fig, ax)

      fig.tight_layout()
      Path(out_filename).parent.mkdir(exist_ok = True, parents = True)
      fig.savefig(out_filename)
      print("Written: " + out_filename)

