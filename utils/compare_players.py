from common.aggregation import date_to_aggregation_date, get_aggregation_dates
from common.data import get_daily_ratings, get_days_with_change
from common.output import get_player_colors, get_timescale_xticks, get_colors_from_scale, \
                          country, last_name, readable_name_and_country, pretty_format
from common.stats import get_stats_for_list

from datetime import date
from matplotlib import pyplot as plt, cm
from pathlib import Path

# ['', 'batting', 'bowling', 'allrounder']
TYPE = ''
# ['', 'test', 'odi', 't20']
FORMAT = 't20'

START_DATE = date(2007, 1, 1)
END_DATE = date(2024, 7, 1)

MAX_RATING = 1000
THRESHOLD = 500

COMPARE_RANKS = [1, 2, 3]
COMPARE_PLAYERS = []
for i, p in enumerate(COMPARE_PLAYERS):
  COMPARE_PLAYERS[i] = p + '.data'

COLOR_BY_COUNTRY = False

# ['', 'monthly', 'quarterly', 'halfyearly', 'yearly', 'fiveyearly', 'decadal']
PLOT_AVERAGES = 'yearly'
PLOT_AVERAGE_KEYS = []
SHOW_CHANGES = []
if COMPARE_PLAYERS:
  for i, p in enumerate(PLOT_AVERAGE_KEYS):
    PLOT_AVERAGE_KEYS[i] = p + '.data'
  for i, p in enumerate(SHOW_CHANGES):
    SHOW_CHANGES[i] = p + '.data'

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
  assert not TYPE == 'allrounder', "COMPARE_RANKS not supported for allrounders"
if COMPARE_PLAYERS:
  assert not COMPARE_RANKS, "Both COMPARE_RANKS and COMPARE_PLAYERS cannot be set"
if COLOR_BY_COUNTRY:
  assert COMPARE_PLAYERS, \
      "COLOR_BY_COUNTRY can only be set when COMPARE_PLAYERS is provided"

if PLOT_AVERAGE_KEYS:
  assert PLOT_AVERAGES, "PLOT_AVERAGE_KEYS provided but no PLOT_AVERAGES"
  assert not set(PLOT_AVERAGE_KEYS) - (set(COMPARE_RANKS) | set(COMPARE_PLAYERS)), \
      "PLOT_AVERAGE_KEYS must be a subset of compare keys to plot"
assert PLOT_AVERAGES in ['', 'monthly', 'quarterly', 'halfyearly', \
                          'yearly', 'fiveyearly', 'decadal']


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

  daily_ratings, daily_ranks = get_daily_ratings(typ, frmt, changed_days_criteria = '', \
                                    allrounders_geom_mean = ALLROUNDERS_GEOM_MEAN)

  compare_stats = get_compare_stats(daily_ratings, daily_ranks, \
                                    COMPARE_PLAYERS, COMPARE_RANKS, START_DATE, END_DATE)
  print("Compare stats built with " + str(len(compare_stats)) + " keys")

  aggregation_dates = []
  if compare_stats and PLOT_AVERAGE_KEYS:
    days_with_change = get_days_with_change(daily_ratings, PLOT_AVERAGES)
    agg_daily_ratings = {d: v for d, v in daily_ratings.items() if d in days_with_change}

    aggregation_dates = get_aggregation_dates(agg_daily_ratings, \
                                              agg_window = PLOT_AVERAGES, \
                                              start_date = START_DATE, \
                                              end_date = END_DATE)
    agg_window_size = aggregation_dates[1] - aggregation_dates[0]

    date_to_agg_date = \
            date_to_aggregation_date(dates = list(agg_daily_ratings.keys()), \
                                      aggregation_dates = aggregation_dates)
    if not aggregation_dates[-1] == END_DATE:
      aggregation_dates.append(END_DATE)

    keys_to_window_counts = {k: {} for k in PLOT_AVERAGE_KEYS}
    for k in PLOT_AVERAGE_KEYS:
      for d in date_to_agg_date:
        if d < START_DATE or d > END_DATE or d not in compare_stats[k]:
          continue
        agg_date = date_to_agg_date[d]
        if agg_date not in keys_to_window_counts[k]:
          keys_to_window_counts[k][agg_date] = []
        keys_to_window_counts[k][agg_date].append(compare_stats[k][d])

    keys_to_avgs = {k: {} for k in PLOT_AVERAGE_KEYS}
    for k in keys_to_window_counts:
      for d in keys_to_window_counts[k]:
        keys_to_avgs[k][d] = get_stats_for_list(keys_to_window_counts[k][d], 'avg')

    print("Aggregate stats built with " + str(len(keys_to_avgs)) + " keys")

  if compare_stats:
    resolution = tuple([12.8, 7.2])
    fig, ax = plt.subplots(figsize = resolution)

    ax.set_title("Comparison of " + pretty_format(frmt, typ) \
                      +("(GEOM)" if typ == 'allrounder' \
                                and ALLROUNDERS_GEOM_MEAN else '') \
                      + "\n" + str(START_DATE) + " to " + str(END_DATE), \
                  fontsize ='xx-large')

    ax.set_ylabel("Rating", fontsize = 'x-large')
    ax.set_ylim(THRESHOLD, MAX_RATING)
    yticks = range(THRESHOLD, MAX_RATING + 1, 50)
    ax.set_yticks(yticks)
    ax.set_yticklabels([str(y) for y in yticks], fontsize ='large')

    ax.set_xlabel("Date", fontsize = 'x-large')
    ax.set_xlim(START_DATE, END_DATE)
    xticks_major, xticks_minor, xticklabels = \
            get_timescale_xticks(START_DATE, END_DATE, format = 'widescreen')
    ax.set_xticks(xticks_major)
    ax.set_xticks(xticks_minor, minor = True)
    ax.set_xticklabels(xticklabels, fontsize ='large')
    
    ax.grid(True, which = 'major', axis = 'both', alpha = 0.6)
    ax.grid(True, which = 'minor', axis = 'both', alpha = 0.3)

    if COMPARE_PLAYERS:
      player_to_color = get_player_colors(COMPARE_PLAYERS, by_country = COLOR_BY_COUNTRY)

      for p in COMPARE_PLAYERS:
        (xs, ys) = [], []
        if p in compare_stats:
          (xs, ys) = zip(*compare_stats[p].items())

        plt.plot(xs, ys, linestyle = '-', linewidth = 5, antialiased = True, \
                          alpha = 0.4, color = player_to_color[p], \
                          label = readable_name_and_country(p))

        if PLOT_AVERAGE_KEYS and p in keys_to_avgs:
          ax.barh(y = keys_to_avgs[p].values(), width = agg_window_size, \
                  align = 'center', left = keys_to_avgs[p].keys(), \
                  height = (MAX_RATING - THRESHOLD) / 40, \
                  color = player_to_color[p], alpha = 0.4)

        if p in SHOW_CHANGES:
          last_r = 0
          for d in compare_stats[p]:
            r = compare_stats[p][d]
            if not last_r == 0 and not r == last_r:
              plt.text(d, r + 10, str(r - last_r), fontsize = 'medium', alpha = 0.8)
            last_r = r

    elif COMPARE_RANKS:
      colors = get_colors_from_scale(len(COMPARE_RANKS))

      for i, rank in enumerate(COMPARE_RANKS):
        (xs, ys) = [], []
        if rank in compare_stats:
          (xs, ys) = zip(*compare_stats[rank].items())

        plt.plot(xs, ys, linestyle = '-', linewidth = 5, antialiased = True, \
                          alpha = 0.4, color = colors[i], label = 'Rank ' + str(rank))

        if PLOT_AVERAGE_KEYS and rank in keys_to_avgs:
          ax.barh(y = keys_to_avgs[rank].values(), width = agg_window_size, \
                  align = 'center', left = keys_to_avgs[rank].keys(), \
                  height = (MAX_RATING - THRESHOLD) / 40, \
                  color = colors[i], alpha = 0.4)

        if rank in SHOW_CHANGES:
          last_r = 0
          for d in compare_stats[rank]:
            r = compare_stats[rank][d]
            if not last_r == 0 and not r == last_r:
              plt.text(d, r + 10, str(r - last_r), fontsize = 'medium', alpha = 0.8)
            last_r = r

    ax.legend(loc = 'best', fontsize = 'large')

    fig.tight_layout()

    comparison_text = ''
    if COMPARE_PLAYERS:
      for p in COMPARE_PLAYERS:
        comparison_text += country(p) + last_name(p) + '_'
    elif COMPARE_RANKS:
      for r in COMPARE_RANKS:
        comparison_text += str(r) + '_'
    out_filename = 'out/images/line/comparison/' + comparison_text \
                    + frmt + '_' + typ \
                    + ("GEOM" if typ == 'allrounder' and ALLROUNDERS_GEOM_MEAN else '') \
                    + '_' + str(START_DATE.year) + '_' + str(END_DATE.year) + '.png'

    Path(out_filename).parent.mkdir(exist_ok = True, parents = True)
    fig.savefig(out_filename)
    print("Written: " + out_filename)
