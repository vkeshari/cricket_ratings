from common.aggregation import date_to_aggregation_date, get_aggregation_dates, \
                                is_aggregation_window_start
from common.data import get_daily_ratings
from common.output import get_timescale_xticks
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
  thresholds_to_plot = RATING_STOPS
else:
  thresholds_to_plot = range(THRESHOLD, MAX_RATING, RATING_STEP)

# ['', 'monthly', 'quarterly', 'halfyearly', 'yearly', 'fiveyearly', 'decadal']
PLOT_AVERAGES = 'yearly'
PLOT_AVERAGE_RATINGS = thresholds_to_plot

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
assert RATING_STEP >= 20, "RATING_STEP must be at least 20"
assert (MAX_RATING - THRESHOLD) % RATING_STEP == 0, \
      "RATING_STEP must be a factor of ratings range"

for r in RATING_STOPS:
  assert r >= THRESHOLD and r <= MAX_RATING, \
      "All values in RATING_STOPS must be between THRESHOLD and MAX_RATING"

if PLOT_AVERAGE_RATINGS:
  assert PLOT_AVERAGES, "PLOT_AVERAGE_RATINGS provided but no PLOT_AVERAGES"
  assert not set(PLOT_AVERAGE_RATINGS) - set(thresholds_to_plot), \
      "PLOT_AVERAGE_RATINGS must be a subset of ratings to plot"
assert PLOT_AVERAGES in ['', 'monthly', 'quarterly', 'halfyearly', \
                          'yearly', 'fiveyearly', 'decadal']

assert CHANGED_DAYS_CRITERIA in ['', 'rating', 'rank', 'either', 'both'], \
        "Invalid CHANGED_DAYS_CRITERIA"

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

  daily_ratings, _ = get_daily_ratings(typ, frmt, \
                            changed_days_criteria = CHANGED_DAYS_CRITERIA, \
                            allrounders_geom_mean = ALLROUNDERS_GEOM_MEAN)

  thresholds_to_counts = {t: {} for t in thresholds_to_plot}
  for t in thresholds_to_plot:
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
    aggregation_dates = get_aggregation_dates(daily_ratings, \
                                              agg_window = PLOT_AVERAGES, \
                                              start_date = START_DATE, \
                                              end_date = END_DATE)
    date_to_agg_date = \
            date_to_aggregation_date(dates = list(daily_ratings.keys()), \
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


  colorscale = cm.tab20
  resolution = tuple([12.8, 7.2])
  fig, ax = plt.subplots(figsize = resolution)

  ax.set_title("No. of " + frmt + ' ' + typ + ' ' + "players above rating" \
                    + "\n" + str(START_DATE) + " to " + str(END_DATE), \
                fontsize ='xx-large')

  color_stops = np.linspace(0, 1, len(thresholds_to_plot) + 1)
  colors = colorscale(color_stops)

  ymax = 9
  for i, t in enumerate(thresholds_to_counts):
    (xs, ys) = zip(*thresholds_to_counts[t].items())
    ymax = max(ymax, max(thresholds_to_counts[t].values()))

    plt.plot(xs, ys, linestyle = '-', linewidth = 3, antialiased = True, \
                      alpha = 0.5, color = colors[i], label = "Rating >= " + str(t))

    if t in PLOT_AVERAGE_RATINGS:
      for j, d in enumerate(aggregation_dates[ : -1]):
        xs = (d, aggregation_dates[j + 1])
        ys = (thresholds_to_avgs[t][d], thresholds_to_avgs[t][d])
        plt.plot(xs, ys, linestyle = '-', linewidth = 10, antialiased = True, \
                        alpha = 0.5, color = colors[i])

  ax.set_ylabel("No. of players above rating", fontsize = 'x-large')
  ax.set_ylim(0, ymax + 1)
  if ymax <= 10:
    yticks = range(0, ymax + 1)
  else:
    yticks = range(0, ymax + 1, 5)
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

  rating_range_text = ''
  for r in thresholds_to_plot:
    rating_range_text += str(r) + '_'
  out_filename = 'out/images/line/aboverating/' + rating_range_text \
                  + (PLOT_AVERAGES + '_' if PLOT_AVERAGES else '') \
                  + frmt + '_' + typ + '_' \
                  + str(START_DATE.year) + '_' + str(END_DATE.year) + '.png'

  Path(out_filename).parent.mkdir(exist_ok = True, parents = True)
  fig.savefig(out_filename)
  print("Written: " + out_filename)