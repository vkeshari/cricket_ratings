from common.data import get_daily_ratings
from common.output import readable_name_and_country, get_player_colors, pretty_format

from datetime import date
from matplotlib import pyplot as plt
from pathlib import Path

import math

# ['batting', 'bowling', 'allrounder']
TYPE = ''
# ['test', 'odi', 't20']
FORMAT = 't20'

MAX_PLAYERS = 20
NUM_TOP = 3

# ['', 'rating', 'rank', 'either', 'both']
CHANGED_DAYS_CRITERIA = 'either'

SHOW_TABLE = True
SHOW_GRAPH = True
COLOR_BY_COUNTRY = True
MAX_NAMES = 10

# Alternate way to calculate allrounder ratings. Use geometric mean of batting and bowling.
ALLROUNDERS_GEOM_MEAN = True

EPOCH = date(1901, 1, 1)

assert TYPE in ['', 'batting', 'bowling', 'allrounder'], "Invalid TYPE provided"
assert FORMAT in ['', 'test', 'odi', 't20'], "Invalid FORMAT provided"
assert NUM_TOP > 0, "NUM_TOP must be positive"
assert MAX_PLAYERS >= NUM_TOP, "MAX_PLAYERS must be at least NUM_TOP"
assert MAX_NAMES <= MAX_PLAYERS, "MAX_NAMES must be at most MAX_PLAYERS"

assert CHANGED_DAYS_CRITERIA in ['', 'rating', 'rank', 'either', 'both']


def get_top_player_stats(daily_ratings, daily_ranks, num_top):
  player_stats = {}

  for d in daily_ranks:
    for p in daily_ranks[d]:
      if p not in player_stats:
        player_stats[p] = {'min_rank': 100, 'max_rating': 0, 'days_at_top': 0, \
                            'max_rating_date' : EPOCH}

      rank = daily_ranks[d][p]
      if rank < player_stats[p]['min_rank']:
        player_stats[p]['min_rank'] = rank

      if rank <= num_top:
        player_stats[p]['days_at_top'] += 1

  for d in daily_ratings:
    for p in daily_ratings[d]:
      if p not in player_stats:
        player_stats[p] = {'min_rank': 100, 'max_rating': 0, 'days_at_top': 0, \
                            'max_rating_date' : EPOCH}

      rating = daily_ratings[d][p]
      if rating > player_stats[p]['max_rating']:
        player_stats[p]['max_rating'] = rating
        player_stats[p]['max_rating_date'] = d

  return player_stats


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

  daily_ratings, daily_ranks = get_daily_ratings(typ, frmt, \
                                    changed_days_criteria = CHANGED_DAYS_CRITERIA, \
                                    allrounders_geom_mean = ALLROUNDERS_GEOM_MEAN)

  top_player_stats = get_top_player_stats(daily_ratings, daily_ranks, NUM_TOP)
  sorted_top_stats = dict(sorted(top_player_stats.items(), \
                                      key = lambda item: (item[1]['days_at_top'], \
                                                          -item[1]['min_rank'],
                                                          item[1]['max_rating']), \
                                      reverse = True))

  if SHOW_TABLE:
    print ("Players by longest time spent in top " + str(NUM_TOP) + ' rankings :' \
            + '\t' + frmt + '\t' + typ)

    for i, p in enumerate(sorted_top_stats):
      days_at_top = sorted_top_stats[p]['days_at_top']
      min_rank = sorted_top_stats[p]['min_rank']
      max_rating = sorted_top_stats[p]['max_rating']
      max_rating_date = sorted_top_stats[p]['max_rating_date']
      print (str(i + 1) + '\tMax Rating: ' + str(max_rating) + '\t\ton\t'
              + str(max_rating_date) + '\t\tBest Rank:\t' \
              + str(min_rank) + '\tDays in top ' + str(NUM_TOP) + ':\t' + str(days_at_top) \
              + '\t' + readable_name_and_country(p))
      if i == MAX_PLAYERS - 1:
        break

  if SHOW_GRAPH:
    resolution = tuple([7.2, 7.2])
    fig, ax = plt.subplots(figsize = resolution)

    title_text = pretty_format(frmt, typ) \
                  + " by no. of days spent in Top " + str(NUM_TOP) + " Ranks"
    ax.set_title(title_text, fontsize ='xx-large')

    ax.set_ylabel("No. of Days", fontsize ='x-large')

    days_list = [s['days_at_top'] for s in sorted_top_stats.values()][ : MAX_PLAYERS]

    ymax = (math.ceil(max(days_list) / 100)) * 105

    ax.set_ylim(0, ymax)
    ystep = 100
    if ymax > 1000:
      ystep = 200
    if ymax > 5000:
      ystep = 500
    yticks = range(0, ymax + 1, ystep)
    ax.set_yticks(yticks)
    ax.set_yticklabels([str(y) for y in yticks], fontsize ='large')

    ax.grid(True, which = 'both', axis = 'y', alpha = 0.8)

    ax.set_xlabel("Ordered players", fontsize ='x-large')
    ax.set_xlim(0, MAX_PLAYERS)
    if MAX_PLAYERS <= 25:
      xstep = 1
    else:
      xstep = 5
    xticks = range(0, MAX_PLAYERS, xstep)
    ax.set_xticks(xticks)
    ax.set_xticklabels([str(x + 1) for x in xticks], fontsize ='large')

    if COLOR_BY_COUNTRY:
      colors = get_player_colors(sorted_top_stats.keys(), by_country = True)
      cols = list(colors.values())[ : MAX_PLAYERS]
    else:
      cols = 'green'
    xs = list(range(len(days_list)))

    ax.bar(xs, days_list, align = 'edge', color = cols, alpha = 0.5, \
              linewidth = 1, edgecolor = 'darkgrey')

    prev_y = 0
    ytext_step = ymax / 40
    if MAX_NAMES > 0:
      for i, p in reversed(list(enumerate(sorted_top_stats.keys()))[ : MAX_NAMES]):
        days_at_top = sorted_top_stats[p]['days_at_top']
        player_text = readable_name_and_country(p) \
                        + ': ' + '{r:3d}'.format(r = days_at_top)
        yloc = max(days_at_top + ytext_step / 5, prev_y + ytext_step)
        plt.text(x = i + 0.5, y = yloc, s = player_text, \
                  alpha = 0.8, fontsize = 'large', \
                  horizontalalignment = 'left', verticalalignment = 'bottom')
        prev_y = yloc

    fig.tight_layout()

    out_filename = 'out/images/bar/timeattop/' \
                    + frmt + '_' + typ + '_' \
                    + ('unfiltered_' if not CHANGED_DAYS_CRITERIA else '') \
                    + 'top' + str(NUM_TOP) + '_' + str(MAX_PLAYERS) + '.png'

    Path(out_filename).parent.mkdir(exist_ok = True, parents = True)
    fig.savefig(out_filename)
    print("Written: " + out_filename)
