from common.data import get_daily_ratings
from common.output import pretty_format
from common.stats import get_stats_for_list

from datetime import date
from matplotlib import pyplot as plt
from pathlib import Path

import numpy as np
import math

# ['', 'batting', 'bowling', 'allrounder']
TYPE = ''
# ['', 'test', 'odi', 't20']
FORMAT = 't20'

# Graph dates
GRAPH_DATES = [date(2024, 1, 1)]

# Upper and lower bounds of ratings to show
THRESHOLD = 500
MAX_RATING = 1000
BIN_SIZE = 50

# ['', 'rating', 'rank', 'either', 'both']
CHANGED_DAYS_CRITERIA = ''

SHOW_BIN_COUNTS = False
SHOW_GRAPH = True
# ['avg', 'median', 'p90', ... ] (See common.stats.get_stats_for_list)
PLOT_STATS = []

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

if PLOT_STATS:
  assert THRESHOLD == 0 and MAX_RATING == 1000, \
      "Ratings range must be 0 to 1000 if PLOT_STATS is provided"

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

  for graph_date in GRAPH_DATES:
    print (graph_date)

    if graph_date not in daily_ratings:
      print ("Skipping " + frmt + ' ' + typ + ": Graph date not found in ratings")
      continue

    day_ratings = daily_ratings[graph_date]
    day_ratings = [d for d in day_ratings.values() \
                      if d > 0 and d >= THRESHOLD and d <= MAX_RATING]
    num_players = len(day_ratings)

    bins = range(THRESHOLD, MAX_RATING + 1, BIN_SIZE)
    bin_counts = np.histogram(day_ratings, bins)[0]
    actual_bins = bins[ : -1]

    if SHOW_BIN_COUNTS:
      print("=== Bin counts (" + frmt + " " + typ + ") on " + str(graph_date) + " ===")
      print("BIN\tCOUNT")

      for i, b in enumerate(actual_bins):
        print ('{b:3d}\t{bc:3d}'.format(b = b, bc = bin_counts[i]))

    if SHOW_GRAPH:
      resolution = tuple([7.2, 7.2])
      fig, ax = plt.subplots(figsize = resolution)

      title_text = "Distribution of " + pretty_format(frmt, typ) \
                    + " by rating\n" + str(graph_date)
      ax.set_title(title_text, fontsize ='xx-large')

      ax.set_ylabel('No. of players', fontsize ='x-large')
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
      ax.hist(day_ratings, bins, align = 'mid', \
                color = graph_color, alpha = 0.5)

      for i, s in enumerate(PLOT_STATS):
        s_loc = get_stats_for_list(day_ratings, s)
        y_ratio = 0.95 - 0.05 * i
        plt.axvline(x = s_loc, ymax = y_ratio, \
                    linestyle = ':', color = 'black', alpha = 0.8)
        plt.text(s_loc + 5, y_ratio * ymax, \
                  s = s + ': ' + '{v:3.0f}'.format(v = s_loc), \
                  color = 'black', alpha = 0.9, fontsize = 'large', \
                  horizontalalignment = 'left', verticalalignment = 'center')

      plt.text(MAX_RATING - 10, ymax * 0.95, \
                s = 'Total players: ' + str(num_players), \
                alpha = 1, fontsize = 'x-large', \
                horizontalalignment = 'right', verticalalignment = 'top')

      fig.tight_layout()

      out_filename = 'out/images/hist/singleday/' + str(THRESHOLD) + '_' \
                      + str(MAX_RATING) + '_' + str(BIN_SIZE) + '_' \
                      + frmt + '_' + typ + '_' \
                      + str(graph_date.year) + '.png'

      Path(out_filename).parent.mkdir(exist_ok = True, parents = True)
      fig.savefig(out_filename)
      print("Written: " + out_filename)
