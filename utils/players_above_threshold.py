from common.data import get_daily_ratings
from common.output import readable_name_and_country

from datetime import date

# ['batting', 'bowling', 'allrounder']
TYPE = 'batting'
# ['test', 'odi', 't20']
FORMAT = 't20'
PLAYERS_DIR = 'players/' + TYPE + '/' + FORMAT

START_DATE = date(2009, 1, 1)
END_DATE = date(2024, 1, 1)

MAX_RATING = 1000
THRESHOLD = 0
RATING_STEP = 100

# ['', 'rating', 'rank', 'either', 'both']
CHANGED_DAYS_CRITERIA = 'either'

# Alternate way to calculate allrounder ratings. Use geometric mean of batting and bowling.
ALLROUNDERS_GEOM_MEAN = True

assert TYPE in ['batting', 'bowling', 'allrounder'], "Invalid TYPE provided"
assert FORMAT in ['test', 'odi', 't20'], "Invalid FORMAT provided"
assert START_DATE < END_DATE, "START_DATE must be earlier than END_DATE"
assert END_DATE <= date.today(), "Future END_DATE requested"

assert MAX_RATING <= 1000, "MAX_RATING must not be greater than 1000"
assert THRESHOLD >= 0 and THRESHOLD < MAX_RATING, \
      "THRESHOLD must be between 0 and MAX_RATING"
assert RATING_STEP >= 20, "RATING_STEP must be at least 20"
assert (MAX_RATING - THRESHOLD) % RATING_STEP == 0, \
      "RATING_STEP must be a factor of ratings range"

assert CHANGED_DAYS_CRITERIA in ['', 'rating', 'rank', 'either', 'both'], \
        "Invalid CHANGED_DAYS_CRITERIA"

print (FORMAT + ' : ' + TYPE)
print (str(START_DATE) + ' : ' + str(END_DATE))

daily_ratings, _ = get_daily_ratings(TYPE, FORMAT, \
                          changed_days_criteria = CHANGED_DAYS_CRITERIA, \
                          allrounders_geom_mean = ALLROUNDERS_GEOM_MEAN)

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

ax.set_title("No. of " + FORMAT + ' ' + TYPE + ' ' + "players above rating" \
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
yticks = range(0, ymax + 1, 5)
ax.set_yticks(yticks)
ax.set_yticklabels([str(y) for y in yticks], fontsize ='large')

ax.set_xlabel("Date", fontsize = 'x-large')
ax.set_xlim(START_DATE, END_DATE)
xtick_yr_range = range(START_DATE.year, END_DATE.year + 1)
if (END_DATE.year - START_DATE.year) > 20:
  xtick_yr_range = range(START_DATE.year, END_DATE.year + 1, 2)
if (END_DATE.year - START_DATE.year) > 50:
  xtick_yr_range = range(START_DATE.year, END_DATE.year + 1, 5)
xticks = [date(yr, 1, 1) for yr in xtick_yr_range]
ax.set_xticks(xticks)
ax.set_xticklabels([str(x.year) for x in xticks], fontsize ='large', rotation = 45)

ax.legend(loc = 'best', fontsize = 'medium')
ax.grid(True, which = 'both', axis = 'both', alpha = 0.5)

fig.tight_layout()
plt.show()
