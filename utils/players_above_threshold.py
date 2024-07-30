from common.aggregation import date_to_aggregation_date, get_aggregation_dates
from common.data import get_daily_ratings, get_days_with_change
from common.output import get_timescale_xticks, get_colors_from_scale, pretty_format
from common.stats import get_stats_for_list

from datetime import date
from matplotlib import pyplot as plt, cm
from pathlib import Path

import numpy as np

# ['', 'batting', 'bowling', 'allrounder']
TYPE = ''
# ['', 'test', 'odi', 't20']
FORMAT = 't20'

START_DATE = date(2007, 1, 1)
END_DATE = date(2024, 7, 1)

MAX_RATING = 1000
THRESHOLD = 500

RATING_STEP = 100
RATING_STOPS = []

if RATING_STOPS:
  THRESHOLDS_TO_PLOT = RATING_STOPS
else:
  THRESHOLDS_TO_PLOT = range(THRESHOLD, MAX_RATING, RATING_STEP)

# ['', 'monthly', 'quarterly', 'halfyearly', 'yearly', 'fiveyearly', 'decadal']
PLOT_AVERAGES = 'yearly'
PLOT_AVERAGE_RATINGS = THRESHOLDS_TO_PLOT

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
assert RATING_STEP >= 20, "RATING_STEP must be at least 20"
assert (MAX_RATING - THRESHOLD) % RATING_STEP == 0, \
      "RATING_STEP must be a factor of ratings range"

for r in RATING_STOPS:
  assert r >= THRESHOLD and r <= MAX_RATING, \
      "All values in RATING_STOPS must be between THRESHOLD and MAX_RATING"

assert THRESHOLDS_TO_PLOT, "THRESHOLDS_TO_PLOT is empty"

if PLOT_AVERAGE_RATINGS:
  assert PLOT_AVERAGES, "PLOT_AVERAGE_RATINGS provided but no PLOT_AVERAGES"
  assert not set(PLOT_AVERAGE_RATINGS) - set(THRESHOLDS_TO_PLOT), \
      "PLOT_AVERAGE_RATINGS must be a subset of THRESHOLDS_TO_PLOT"
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

  daily_ratings, _ = get_daily_ratings(typ, frmt, changed_days_criteria = '', \
                            allrounders_geom_mean = ALLROUNDERS_GEOM_MEAN)

  thresholds_to_counts = {t: {} for t in THRESHOLDS_TO_PLOT}
  for t in THRESHOLDS_TO_PLOT:
    for d in daily_ratings:
      if d < START_DATE or d > END_DATE:
        continue
      thresholds_to_counts[t][d] = 0
      for rating in daily_ratings[d].values():
        if rating >= t:
          thresholds_to_counts[t][d] += 1
  print("Counts above thresholds built for " \
            + str(len(thresholds_to_counts)) + " thresholds")

  aggregation_dates = []
  if PLOT_AVERAGE_RATINGS:
    days_with_change = get_days_with_change(daily_ratings, PLOT_AVERAGES, \
                                            consider_player_keys = True)
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

    thresholds_to_window_counts = {t: {} for t in PLOT_AVERAGE_RATINGS}
    for t in PLOT_AVERAGE_RATINGS:
      for d in date_to_agg_date:
        if d < START_DATE or d > END_DATE:
          continue
        agg_date = date_to_agg_date[d]
        if agg_date not in thresholds_to_window_counts[t]:
          thresholds_to_window_counts[t][agg_date] = []
        thresholds_to_window_counts[t][agg_date].append(thresholds_to_counts[t][d])

    thresholds_to_avgs = {t: {} for t in PLOT_AVERAGE_RATINGS}
    for t in thresholds_to_window_counts:
      for d in thresholds_to_window_counts[t]:
        thresholds_to_avgs[t][d] = \
                get_stats_for_list(thresholds_to_window_counts[t][d], 'avg')

    print("Aggregate stats built with " + str(len(thresholds_to_avgs)) + " keys")


  resolution = tuple([12.8, 7.2])
  fig, ax = plt.subplots(figsize = resolution)

  ax.set_title("No. of " + pretty_format(frmt, typ) + " Above Rating" \
                    + "\n" + str(START_DATE) + " to " + str(END_DATE), \
                fontsize ='xx-large')

  colors = get_colors_from_scale(len(THRESHOLDS_TO_PLOT))

  ymax = 9
  for t in thresholds_to_counts:
    ymax = max(ymax, max(thresholds_to_counts[t].values()))
  ymax += 1

  for i, t in enumerate(thresholds_to_counts):
    (xs, ys) = zip(*thresholds_to_counts[t].items())
    plt.plot(xs, ys, linestyle = '-', linewidth = 3, antialiased = True, \
                      alpha = 0.3, color = colors[i], label = "Rating >= " + str(t))

    if PLOT_AVERAGE_RATINGS and t in thresholds_to_avgs:
      ax.barh(y = thresholds_to_avgs[t].values(), width = agg_window_size, \
              align = 'center', left = thresholds_to_avgs[t].keys(), \
              height = ymax / 40, color = colors[i], alpha = 0.5)

  ax.set_ylabel("No. of players above rating", fontsize = 'x-large')
  ax.set_ylim(0, ymax)
  if ymax <= 10:
    yticks = range(0, ymax)
  else:
    yticks = range(0, ymax, 5)
  ax.set_yticks(yticks)
  ax.set_yticklabels([str(y) for y in yticks], fontsize ='large')

  ax.set_xlabel("Date", fontsize = 'x-large')
  ax.set_xlim(START_DATE, END_DATE)

  xticks_major, xticks_minor, xticklabels = \
          get_timescale_xticks(START_DATE, END_DATE, format = 'widescreen')
  ax.set_xticks(xticks_major)
  ax.set_xticks(xticks_minor, minor = True)
  ax.set_xticklabels(xticklabels, fontsize ='large')

  ax.legend(loc = 'best', fontsize = 'large')
  ax.grid(True, which = 'major', axis = 'both', alpha = 0.6)
  ax.grid(True, which = 'minor', axis = 'both', alpha = 0.3)

  fig.tight_layout()

  rating_range_text = ''
  for r in THRESHOLDS_TO_PLOT:
    rating_range_text += str(r) + '_'
  out_filename = 'out/images/line/aboverating/' + rating_range_text \
                  + (PLOT_AVERAGES + '_' if PLOT_AVERAGES else '') \
                  + frmt + '_' + typ + '_' \
                  + str(START_DATE.year) + '_' + str(END_DATE.year) + '.png'

  Path(out_filename).parent.mkdir(exist_ok = True, parents = True)
  fig.savefig(out_filename)
  print("Written: " + out_filename)
