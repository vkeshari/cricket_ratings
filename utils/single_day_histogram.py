from common.data import get_daily_ratings
from common.output import get_player_colors, readable_name_and_country

from datetime import date
from matplotlib import pyplot as plt

import numpy as np
import math

# ['batting', 'bowling', 'allrounder']
TYPE = 'batting'
# ['test', 'odi', 't20']
FORMAT = 't20'

# Graph date range
GRAPH_DATE = date(2024, 7, 1)

# Upper and lower bounds of ratings to show
THRESHOLD = 500
MAX_RATING = 1000
BIN_SIZE = 50

# ['', 'rating', 'rank', 'either', 'both']
CHANGED_DAYS_CRITERIA = ''

SHOW_BIN_COUNTS = False
SHOW_GRAPH = True

# Alternate way to calculate allrounder ratings. Use geometric mean of batting and bowling.
ALLROUNDERS_GEOM_MEAN = True

assert TYPE in ['batting', 'bowling', 'allrounder'], "Invalid TYPE provided"
assert FORMAT in ['test', 'odi', 't20'], "Invalid FORMAT provided"

assert MAX_RATING <= 1000, "MAX_RATING must not be greater than 1000"
assert THRESHOLD >= 0 and THRESHOLD < MAX_RATING, \
      "THRESHOLD must be between 0 and MAX_RATING"

assert CHANGED_DAYS_CRITERIA in ['', 'rating', 'rank', 'either', 'both']

assert BIN_SIZE >= 10 and BIN_SIZE <= 100, "BIN_SIZE should be between 10 and 100"
assert (MAX_RATING - THRESHOLD) % BIN_SIZE == 0, \
      "BIN_SIZE should be a factor of ratings range"

print (FORMAT + '\t' + TYPE)
print (GRAPH_DATE)
print (str(THRESHOLD) + ' : ' + str(MAX_RATING))

daily_ratings, _ = get_daily_ratings(TYPE, FORMAT, \
                          changed_days_criteria = CHANGED_DAYS_CRITERIA, \
                          allrounders_geom_mean = ALLROUNDERS_GEOM_MEAN)

if GRAPH_DATE in daily_ratings:

  day_ratings = daily_ratings[GRAPH_DATE]
  day_ratings = [d for d in day_ratings.values() if d >= THRESHOLD and d <= MAX_RATING]
  num_players = len(day_ratings)

  bins = range(THRESHOLD, MAX_RATING + 1, BIN_SIZE)
  bin_counts = np.histogram(day_ratings, bins)[0]
  actual_bins = bins[ : -1]

  if SHOW_BIN_COUNTS:
    print("=== Bin counts (" + FORMAT + " " + TYPE + ") on " + str(GRAPH_DATE) + " ===")
    print("BIN\tCOUNT")

    for i, b in enumerate(actual_bins):
      print ('{b:3d}\t{bc:3d}'.format(b = b, bc = bin_counts[i]))

  if SHOW_GRAPH:
    resolution = tuple([7.2, 7.2])
    fig, ax = plt.subplots(figsize = resolution)

    title_text = "Distribution of " + FORMAT + " " + TYPE \
                  + " players by rating\n" + str(GRAPH_DATE)
    ax.set_title(title_text, fontsize ='xx-large')

    ax.set_ylabel('No. of players', fontsize ='x-large')
    ymax = math.ceil(max(bin_counts) / 10) * 10
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

    ax.hist(day_ratings, bins, align = 'mid', \
              color = 'blue', alpha = 0.5)

    plt.text(MAX_RATING - 10, ymax * 0.95, \
              s = 'Total players: ' + str(num_players), \
              alpha = 1, fontsize = 'x-large', \
              horizontalalignment = 'right', verticalalignment = 'top')

    fig.tight_layout()
    plt.show()
