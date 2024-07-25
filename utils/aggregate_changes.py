from common.data import get_daily_ratings
from common.output import pretty_format
from common.stats import get_stats_for_list

from datetime import date
from matplotlib import pyplot as plt
from pathlib import Path

import numpy as np

# ['batting', 'bowling']
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

SHOW_STATS = True

REMOVE_MISSED_GAME_DROPS = True
SUSPICION_RANGE = 0.15
SHOW_DEBUG_GRAPH = True
X_MAX = 5

# Alternate way to calculate allrounder ratings. Use geometric mean of batting and bowling.
ALLROUNDERS_GEOM_MEAN = True

assert TYPE in ['', 'batting', 'bowling'], "Invalid TYPE provided"
assert FORMAT in ['', 'test', 'odi', 't20'], "Invalid FORMAT provided"

assert START_DATE < END_DATE, "START_DATE must be earlier than END_DATE"
assert END_DATE <= date.today(), "Future END_DATE requested"

assert MAX_RATING <= 1000, "MAX_RATING must not be greater than 1000"
assert THRESHOLD >= 0 and THRESHOLD < MAX_RATING, \
      "THRESHOLD must be between 0 and MAX_RATING"

assert CHANGED_DAYS_CRITERIA in ['', 'rating', 'rank', 'either', 'both']

assert SUSPICION_RANGE > 0 and SUSPICION_RANGE < 5, \
      "SUSPICION_RANGE must be between 0 and 5"
if SHOW_DEBUG_GRAPH:
  assert REMOVE_MISSED_GAME_DROPS, \
        "Must set REMOVE_MISSED_GAME_DROPS if SHOW_DEBUG_GRAPH is requested"
assert X_MAX > 0, "X_MAX for graph must be greater than 0"


def get_drop_pct(d, frmt):
  if frmt == 'test' or d.year >= 2022:
    return 1.0
  if frmt == 'odi' and d.year < 2022:
    return 0.5
  if frmt == 't20' and d.year < 2022:
    return 2.0
  return 0.0

def is_possible_missed_drop(f, d, frmt):
  pd = -f * 100
  drop_pct = get_drop_pct(d, frmt)
  sus_pct = drop_pct * SUSPICION_RANGE
  return pd > (drop_pct - sus_pct) and pd < (drop_pct + sus_pct)

def is_possible_border_drop(f, d, frmt):
  pd = -f * 100
  drop_pct = get_drop_pct(d, frmt)
  sus_pct = drop_pct * SUSPICION_RANGE
  if frmt == 'test' or d.year >= 2022:
    return pd > (drop_pct - 2 * sus_pct) and pd < (drop_pct - sus_pct) \
            or pd > (drop_pct + sus_pct) and pd < (drop_pct + 2 * sus_pct)


def show_aggregate_stats(changes, neg = False):
  print ("Count:\t{c:6d}".format(c = len(changes)))
  print ("Total:\t{t:6d}".format(t = sum(changes)))
  print ("Avg:\t{a:6.2f}".format(a = get_stats_for_list(changes, 'avg')))
  print ("P10:\t{p:6d}".format(p = get_stats_for_list(changes, ('p90' if neg else 'p10'))))
  print ("P25:\t{p:6d}".format(p = get_stats_for_list(changes, ('p75' if neg else 'p25'))))
  print ("P50:\t{p:6d}".format(p = get_stats_for_list(changes, ('p50' if neg else 'p50'))))
  print ("P75:\t{p:6d}".format(p = get_stats_for_list(changes, ('p25' if neg else 'p75'))))
  print ("P90:\t{p:6d}".format(p = get_stats_for_list(changes, ('p10' if neg else 'p90'))))


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
          change_frac = change / last_rating
          if not change == 0:
            all_changes.append((d, p, rating, change, change_frac))
      last_player_ratings[p] = daily_ratings[d][p]

  all_changes = sorted(all_changes, key = lambda c: c[3], reverse = True)

  daily_gains = [c for (_, _, _, c, _) in all_changes if c > 0]
  daily_drops = [c for (_, _, _, c, _) in all_changes if c < 0]

  pct_gains = [cf * 100 for (_, _, _, c, cf) in all_changes if c > 0]
  pct_drops = [cf * 100 for (_, _, _, c, cf) in all_changes if c < 0]

  if REMOVE_MISSED_GAME_DROPS:
    drops = [c for c in all_changes if c[3] < 0]
    regular_drops = []
    suspicious_drops = []
    border_drops = []
    for d in drops:
      dat = d[0]
      change = d[3]
      change_frac = d[4]
      if is_possible_missed_drop(change_frac, dat, frmt):
        suspicious_drops.append(d)
      elif is_possible_border_drop(change_frac, dat, frmt):
        border_drops.append(d)
      else:
        regular_drops.append(d)

    num_border_avg = int(len(border_drops) / 2)

    rng = np.random.default_rng()
    rng.shuffle(suspicious_drops)
    suspicious_drops = suspicious_drops[ : num_border_avg]

    filtered_drops = regular_drops + border_drops + suspicious_drops
    abs_filtered_drops = [d[3] for d in filtered_drops]
    pct_filtered_drops = [d[4] * 100 for d in filtered_drops]

    daily_drops = sorted(abs_filtered_drops)

    if SHOW_DEBUG_GRAPH:
      resolution = tuple([12.8, 6.4])
      fig, axs = plt.subplots(nrows = 1, ncols = 2, figsize = resolution)

      axs[0].set_title(pretty_format(frmt, typ) + ' % Changes : Before')
      axs[1].set_title(pretty_format(frmt, typ) + ' % Changes : After')

      bins = np.linspace(-X_MAX, X_MAX, 51)

      max_pct_drop = max(np.histogram(pct_drops, bins = bins)[0])

      xticks_major = np.linspace(-X_MAX, X_MAX, 11)
      xticks_minor = np.linspace(-X_MAX, X_MAX, 51)
      for ax in axs:
        ax.set_ylim(0, max_pct_drop)

        ax.set_xlim(-X_MAX, X_MAX)
        ax.set_xticks(xticks_major)
        ax.set_xticks(xticks_minor, minor = True)
        ax.grid(True, which = 'major', axis = 'both', alpha = 0.8)
        ax.grid(True, which = 'minor', axis = 'x', alpha = 0.4)

      axs[0].hist(pct_gains + pct_drops, bins = bins)
      axs[1].hist(pct_gains + pct_filtered_drops, bins = bins)

      fig.tight_layout()
      
      out_filename = 'out/images/bar/singledayfix/' \
                + str(frmt) + '_' + str(typ) + '_' \
                + '{s:.2f}'.format(s = SUSPICION_RANGE) + '_' \
                + str(START_DATE.year) + '_' \
                + str(END_DATE.year) + '.png'

      Path(out_filename).parent.mkdir(exist_ok = True, parents = True)
      fig.savefig(out_filename)
      print("\nWritten: " + out_filename)

  if SHOW_STATS:
    print ("\n=== GAINS ===")
    show_aggregate_stats(daily_gains)
    print ("\n=== DROPS ===")
    show_aggregate_stats(daily_drops, neg = True)
    print ()
