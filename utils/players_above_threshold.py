from common.data import get_daily_ratings
from common.output import get_timescale_xticks

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

RATING_STEP = 100
RATING_STOPS = []

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

  if RATING_STOPS:
    thresholds_to_plot = RATING_STOPS
  else:
    thresholds_to_plot = range(THRESHOLD, MAX_RATING, RATING_STEP)
  thresholds_to_counts = {t: {} for t in thresholds_to_plot}
  for t in thresholds_to_plot:
    for d in daily_ratings:
      thresholds_to_counts[t][d] = 0
      for rating in daily_ratings[d].values():
        if rating >= t:
          thresholds_to_counts[t][d] += 1


  from matplotlib import pyplot as plt, cm
  import numpy as np

  colorscale = cm.tab20
  resolution = tuple([12.8, 7.2])
  fig, ax = plt.subplots(figsize = resolution)

  ax.set_title("No. of " + frmt + ' ' + typ + ' ' + "players above rating" \
                    + "\n" + str(START_DATE) + " to " + str(END_DATE), \
                fontsize ='xx-large')

  color_stops = np.linspace(0, 1, len(thresholds_to_plot) + 1)
  colors = colorscale(color_stops)

  ymax = 0
  for i, t in enumerate(thresholds_to_counts):
    (xs, ys) = zip(*thresholds_to_counts[t].items())
    ymax = max(ymax, max(thresholds_to_counts[t].values()))

    plt.plot(xs, ys, linestyle = '-', linewidth = 3, antialiased = True, \
                      alpha = 0.5, color = colors[i], label = "Rating >= " + str(t))

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
                  + frmt + '_' + typ + '_' \
                  + str(START_DATE.year) + '_' + str(END_DATE.year) + '.png'

  Path(out_filename).parent.mkdir(exist_ok = True, parents = True)
  fig.savefig(out_filename)
  print("Written: " + out_filename)
