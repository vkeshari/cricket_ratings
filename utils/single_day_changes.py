from common.data import get_daily_ratings
from common.output import readable_name_and_country, pretty_format, get_type_color

from datetime import date
from matplotlib import pyplot as plt
from pathlib import Path

import math
import numpy as np

# ['batting', 'bowling', 'allrounder']
TYPE = ''
# ['test', 'odi', 't20']
FORMAT = 't20'

# Graph date range
START_DATE = date(2007, 1, 1)
END_DATE = date(2024, 7, 1)

# Upper and lower bounds of ratings to show
THRESHOLD = 500
MAX_RATING = 1000

# ['', 'rating', 'rank', 'either', 'both']
CHANGED_DAYS_CRITERIA = 'rating'

SHOW_TOP_CHANGES = False
NUM_SHOW = 20

SHOW_GRAPH = True
LOG_SCALE = False
SHOW_PERCENTAGES = False
MAX_CHANGE = 100
NUM_BINS = 40

# Alternate way to calculate allrounder ratings. Use geometric mean of batting and bowling.
ALLROUNDERS_GEOM_MEAN = True

assert TYPE in ['', 'batting', 'bowling', 'allrounder'], "Invalid TYPE provided"
assert FORMAT in ['', 'test', 'odi', 't20'], "Invalid FORMAT provided"
assert START_DATE < END_DATE, "START_DATE must be earlier than END_DATE"
assert END_DATE <= date.today(), "Future END_DATE requested"

assert MAX_RATING <= 1000, "MAX_RATING must not be greater than 1000"
assert THRESHOLD >= 0 and THRESHOLD < MAX_RATING, \
      "THRESHOLD must be between 0 and MAX_RATING"

assert CHANGED_DAYS_CRITERIA in ['', 'rating', 'rank', 'either', 'both']

assert NUM_SHOW >= 5, "NUM_SHOW should be at least 5"

assert NUM_BINS >= 10 and NUM_BINS <= 100, "NUM_BINS must be between 10 and 100"
assert MAX_CHANGE >= 1 and MAX_CHANGE <= 500, "MAX_CHANGE must be between 1 and 500"
if SHOW_PERCENTAGES or LOG_SCALE:
  assert SHOW_GRAPH, "SHOW_PERCENTAGES or LOG_SCALE requested without SHOW_GRAPH"


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
  print (frmt + '\t' + typ)
  print (str(START_DATE) + ' to ' + str(END_DATE))
  print (str(THRESHOLD) + ' : ' + str(MAX_RATING))

  daily_ratings, _ = get_daily_ratings(typ, frmt, \
                            changed_days_criteria = CHANGED_DAYS_CRITERIA, \
                            allrounders_geom_mean = ALLROUNDERS_GEOM_MEAN)

  first_date = min(daily_ratings.keys())
  last_date = max(daily_ratings.keys())

  all_changes = []
  last_player_ratings = {}
  for d in daily_ratings:
    for p in daily_ratings[d]:
      if p not in last_player_ratings:
        last_player_ratings[p] = 0
      if last_player_ratings[p] > 0:
        rating = daily_ratings[d][p]
        last_rating = last_player_ratings[p]
        if last_rating >= THRESHOLD:
          change = rating - last_rating
          if not change == 0:
            all_changes.append((change, rating, d, p))
      last_player_ratings[p] = daily_ratings[d][p]

  all_changes = sorted(all_changes, key = lambda c: c[0], reverse = True)

  top_increases = all_changes[ : NUM_SHOW]
  top_decreases = reversed(all_changes[-NUM_SHOW : ])

  if SHOW_TOP_CHANGES:
    print()
    print("Top daily rating gains")
    print("Gain\tRating\tDate\tPlayer")
    for c, r, d, p in top_increases:
      print('{c:3d}\t{r:3d}\t{d}\t{p}'.format(c = c, r = r, d = str(d), \
                                              p = readable_name_and_country(p)))
    print()
    print("Top daily rating drops")
    print("Drop\tRating\tDate\tPlayer")
    for c, r, d, p in top_decreases:
      print('{c:3d}\t{r:3d}\t{d}\t{p}'.format(c = c, r = r, d = str(d), \
                                              p = readable_name_and_country(p)))


  if SHOW_GRAPH:
    resolution = tuple([7.2, 7.2])

    fig, ax = plt.subplots(figsize = resolution)

    if SHOW_PERCENTAGES:
      changes = []
      for i, (c, _, _, _) in enumerate(all_changes):
        if i == 0:
          continue
        prev_r = all_changes[i - 1][1]
        pct_change = c * 100 / prev_r
        changes.append(pct_change)
    else:
      changes = [c[0] for c in all_changes]

    change_bins = np.linspace(-MAX_CHANGE, MAX_CHANGE, NUM_BINS)
    change_intervals = np.histogram(changes, change_bins)[0]
    ymax = math.ceil(max(change_intervals) / 1000) * 1000

    title = 'Distribution of single-day rating changes\n' \
            + pretty_format(frmt, typ) \
            + ' (' + str(START_DATE) + ' to ' + str(END_DATE) + ')'
    ax.set_title(title, fontsize ='xx-large')

    if SHOW_PERCENTAGES:
      ax.set_xlabel('Daily Rating Percent Change', fontsize = 'x-large')
    else:
      ax.set_xlabel('Daily Rating Change', fontsize = 'x-large')
    ax.set_ylabel('No. of changes', fontsize = 'x-large')

    ax.set_xlim(-MAX_CHANGE, MAX_CHANGE)
    xticks_major = np.linspace(-MAX_CHANGE, MAX_CHANGE, 5)
    xticks_minor = np.linspace(-MAX_CHANGE, MAX_CHANGE, 21)
    ax.set_xticks(xticks_major)
    ax.set_xticks(xticks_minor, minor = True)
    ax.set_xticklabels(['{v:3.0f}'.format(v = x) for x in xticks_major], fontsize ='large')

    if LOG_SCALE:
      plt.yscale('log')
      ax.set_ylim(1, ymax)
      yticks = []
      for p in range(0, 6):
        stop = int(math.pow(10, p))
        if stop <= ymax:
          yticks.append(int(math.pow(10, p)))
    else:
      ax.set_ylim(0, ymax)
      ystep = int(ymax / 10)
      yticks = range(0, ymax, ystep)

    ax.set_yticks(yticks)
    ax.set_yticklabels([str(y) for y in yticks], fontsize ='large')

    ax.grid(True, which = 'major', axis = 'both', alpha = 0.6)
    ax.grid(True, which = 'minor', axis = 'both', alpha = 0.3)

    ax.hist(changes, bins = change_bins, cumulative = False, \
              align = 'mid', color = get_type_color(typ), alpha = 0.5)

    half = MAX_CHANGE / 2
    full = MAX_CHANGE
    plus_half = len([c for c in changes if c >= half])
    minus_half = len([c for c in changes if c <= -half])
    plus_full = len([c for c in changes if c >= full])
    minus_full = len([c for c in changes if c <= -full])
    plt.text(MAX_CHANGE / 10, ymax * 0.95, \
              s = '{v:3.0f}'.format(v = half) + "+ single-day gains: " \
                      + '{r:4d}'.format(r = plus_half), \
              fontsize = 'large', alpha = 0.8)
    plt.text(MAX_CHANGE / 10, ymax * 0.90, \
              s = '{v:3.0f}'.format(v = half) + "+ single-day drops: " \
                      + '{r:4d}'.format(r = minus_half), \
              fontsize = 'large', alpha = 0.8)
    plt.text(MAX_CHANGE / 10, ymax * 0.85, \
              s = '{v:3.0f}'.format(v = full) + "+ single-day gains: " \
                      + '{r:4d}'.format(r = plus_full), \
              fontsize = 'large', alpha = 0.8)
    plt.text(MAX_CHANGE / 10, ymax * 0.80, \
              s = '{v:3.0f}'.format(v = full) + "+ single-day drops: " \
                      + '{r:4d}'.format(r = minus_full), \
              fontsize = 'large', alpha = 0.8)

    fig.tight_layout()

    out_filename = 'out/images/bar/singleday/' + ('PCT_' if SHOW_PERCENTAGES else '') \
                    + frmt + '_' + typ + '_' \
                    + str(START_DATE.year) + '_' + str(END_DATE.year) + '.png'

    Path(out_filename).parent.mkdir(exist_ok = True, parents = True)
    fig.savefig(out_filename)
    print("Written: " + out_filename)
