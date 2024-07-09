from common.data import get_daily_ratings
from common.output import get_player_colors, get_timescale_xticks, \
                          country, last_name, readable_name_and_country

from datetime import date
from pathlib import Path

# ['batting', 'bowling', 'allrounder']
TYPE = 'batting'
# ['test', 'odi', 't20']
FORMAT = 't20'

START_DATE = date(2007, 1, 1)
END_DATE = date(2024, 7, 1)

MAX_RATING = 1000
THRESHOLD = 500

COMPARE_RANKS = [1, 2, 3]
COMPARE_PLAYERS = []
COLOR_BY_COUNTRY = False

# ['', 'rating', 'rank', 'either', 'both']
CHANGED_DAYS_CRITERIA = ''

# Alternate way to calculate allrounder ratings. Use geometric mean of batting and bowling.
ALLROUNDERS_GEOM_MEAN = True

if TYPE:
  assert TYPE in ['batting', 'bowling', 'allrounder'], "Invalid TYPE provided"
if FORMAT:
  assert FORMAT in ['test', 'odi', 't20'], "Invalid FORMAT provided"
assert START_DATE < END_DATE, "START_DATE must be earlier than END_DATE"
assert END_DATE <= date.today(), "Future END_DATE requested"

assert MAX_RATING <= 1000, "MAX_RATING must not be greater than 1000"
assert THRESHOLD >= 0 and THRESHOLD < MAX_RATING, \
      "THRESHOLD must be between 0 and MAX_RATING"

for r in COMPARE_RANKS:
  assert r > 0 and r <= 10, "Each rank in COMPARE_RANKS must be between 1 and 10"
if COMPARE_RANKS:
  assert not COMPARE_PLAYERS, "Both COMPARE_RANKS and COMPARE_PLAYERS cannot be set"
if COMPARE_PLAYERS:
  assert not COMPARE_RANKS, "Both COMPARE_RANKS and COMPARE_PLAYERS cannot be set"
if COLOR_BY_COUNTRY:
  assert COMPARE_PLAYERS, \
      "COLOR_BY_COUNTRY can only be set when COMPARE_PLAYERS is provided"

assert CHANGED_DAYS_CRITERIA in ['', 'rating', 'rank', 'either', 'both'], \
        "Invalid CHANGED_DAYS_CRITERIA"

for i, p in enumerate(COMPARE_PLAYERS):
  COMPARE_PLAYERS[i] = p + '.data'

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
  print (str(START_DATE) + ' : ' + str(END_DATE))

  def get_compare_stats(daily_ratings, daily_ranks, \
                          compare_players, compare_ranks, start_date, end_date):
    if compare_players and compare_ranks:
      print ("Both players and ranks list provided")
      return {}
    if not daily_ratings or not daily_ranks:
      print ("Daily ratings or rankings are empty")
      return {}
    if not daily_ratings.keys() == daily_ranks.keys():
      print ("Key mismatch between daily ratings and ranks")
      return {}

    invalid_players = compare_players
    for d in daily_ratings:
      invalid_players = invalid_players - daily_ratings[d].keys()
      if not invalid_players:
        break
    if invalid_players:
      print("Invalid player name(s)")
      print(invalid_players)
      return {}

    compare_stats = {}
    for d in daily_ratings:
      if d < start_date or d > end_date:
        continue

      for p in daily_ratings[d]:
        rating = daily_ratings[d][p]
        rank = daily_ranks[d][p]

        if p in compare_players:
          if p not in compare_stats:
            compare_stats[p] = {}
          compare_stats[p][d] = rating
        elif rank in compare_ranks:
          if rank not in compare_stats:
            compare_stats[rank] = {}
          compare_stats[rank][d] = rating

    return compare_stats

  daily_ratings, daily_ranks = get_daily_ratings(typ, frmt, \
                                    changed_days_criteria = CHANGED_DAYS_CRITERIA, \
                                    allrounders_geom_mean = ALLROUNDERS_GEOM_MEAN)

  compare_stats = get_compare_stats(daily_ratings, daily_ranks, \
                                    COMPARE_PLAYERS, COMPARE_RANKS, START_DATE, END_DATE)
  print("Compare stats built with " + str(len(compare_stats)) + " keys")


  from matplotlib import pyplot as plt, cm
  import numpy as np

  resolution = tuple([12.8, 7.2])
  fig, ax = plt.subplots(figsize = resolution)

  ax.set_title("Comparison of " + frmt + ' ' + typ + ' ' + "players" \
                    + "\n" + str(START_DATE) + " to " + str(END_DATE), \
                fontsize ='xx-large')

  if COMPARE_PLAYERS:
    player_to_color = get_player_colors(COMPARE_PLAYERS, by_country = COLOR_BY_COUNTRY)

    for i, p in enumerate(COMPARE_PLAYERS):
      (xs, ys) = [], []
      if p in compare_stats:
        (xs, ys) = zip(*compare_stats[p].items())

      plt.plot(xs, ys, linestyle = '-', linewidth = 5, antialiased = True, \
                        alpha = 0.5, color = player_to_color[p], \
                        label = readable_name_and_country(p))

  elif COMPARE_RANKS:
    colors = list(get_player_colors(COMPARE_RANKS).values())

    for i, rank in enumerate(COMPARE_RANKS):
      (xs, ys) = [], []
      if rank in compare_stats:
        (xs, ys) = zip(*compare_stats[rank].items())

      plt.plot(xs, ys, linestyle = '-', linewidth = 3, antialiased = True, \
                        alpha = 0.5, color = colors[i], label = 'Rank ' + str(rank))

  ax.set_ylabel("Rating", fontsize = 'x-large')
  ax.set_ylim(THRESHOLD, MAX_RATING)
  yticks = range(THRESHOLD, MAX_RATING + 1, 50)
  ax.set_yticks(yticks)
  ax.set_yticklabels([str(y) for y in yticks], fontsize ='large')

  ax.set_xlabel("Date", fontsize = 'x-large')
  ax.set_xlim(START_DATE, END_DATE)
  xticks, xticklabels = get_timescale_xticks(START_DATE, END_DATE, format = 'widescreen')
  ax.set_xticks(xticks)
  ax.set_xticklabels(xticklabels, fontsize ='large', rotation = 45)

  ax.legend(loc = 'best', fontsize = 'medium')
  ax.grid(True, which = 'both', axis = 'both', alpha = 0.5)

  fig.tight_layout()

  comparison_text = ''
  if COMPARE_PLAYERS:
    for p in COMPARE_PLAYERS:
      comparison_text += country(p) + last_name(p) + '_'
  elif COMPARE_RANKS:
    for r in COMPARE_RANKS:
      comparison_text += str(r) + '_'
  out_filename = 'out/images/line/comparison/' + comparison_text \
                  + frmt + '_' + typ + '_' \
                  + str(START_DATE.year) + '_' + str(END_DATE.year) + '.png'

  Path(out_filename).parent.mkdir(exist_ok = True, parents = True)
  fig.savefig(out_filename)
  print("Written: " + out_filename)
