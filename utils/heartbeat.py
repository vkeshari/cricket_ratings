from common.data import get_daily_ratings
from common.output import get_timescale_xticks, pretty_format, resolution_by_span

from datetime import date, timedelta
from pathlib import Path
from matplotlib import pyplot as plt

import numpy as np

ONE_YEAR = timedelta(days = 365)

START_DATE = date(2010, 1, 1)
END_DATE = date(2020, 1, 1)

# ['', 'rating', 'rank', 'either', 'both']
CHANGED_DAYS_CRITERIA = 'rating'

# Alternate way to calculate allrounder ratings. Use geometric mean of batting and bowling.
ALLROUNDERS_GEOM_MEAN = True

assert START_DATE < END_DATE, "START_DATE must be earlier than END_DATE"
assert END_DATE <= date.today(), "Future END_DATE requested"

assert CHANGED_DAYS_CRITERIA in ['', 'rating', 'rank', 'either', 'both'], \
        "Invalid CHANGED_DAYS_CRITERIA"


typ = 'batting'
formats = ['t20', 'odi', 'test']

days_by_format = {}
for frmt in formats:
  print (frmt + ' : ' + typ)
  print (str(START_DATE) + ' : ' + str(END_DATE))

  daily_ratings, _ = get_daily_ratings(typ, frmt, \
                            changed_days_criteria = CHANGED_DAYS_CRITERIA, \
                            allrounders_geom_mean = ALLROUNDERS_GEOM_MEAN)

  rating_days = [d for d in sorted(daily_ratings.keys()) \
                  if d >= START_DATE and d <= END_DATE]
  days_by_format[frmt] = rating_days

resolution, aspect_ratio = resolution_by_span(START_DATE, END_DATE)
fig, ax = plt.subplots(figsize = resolution)

title = 'Days with Rating Change by Format\n' \
          + '(' + str(START_DATE) + ' to ' + str(END_DATE) + ')'
ax.set_title(title, fontsize ='x-large')

ax.set_xlabel('Year', fontsize ='x-large')
ax.set_ylabel('Format', fontsize ='x-large')

ax.set_xlim(START_DATE, END_DATE)
xticks_major, xticks_minor, xticklabels = \
        get_timescale_xticks(START_DATE, END_DATE, format = aspect_ratio)
ax.set_xticks(xticks_major)
ax.set_xticks(xticks_minor, minor = True)
ax.set_xticklabels(xticklabels, fontsize ='large')

ymax = 1
ax.set_ylim(0, ymax)
yticks = np.linspace(0, ymax, len(formats) + 2)
ax.set_yticks(yticks)

format_titles = [''] + [pretty_format(f) for f in formats] + ['']
ax.set_yticklabels(format_titles, fontsize = 'large')

ax.grid(True, which = 'major', axis = 'both', alpha = 0.6)
ax.grid(True, which = 'minor', axis = 'both', alpha = 0.3)

if END_DATE - START_DATE > 2 * ONE_YEAR:
  dot_alpha = 0.1
else:
  dot_alpha = 0.3
for i, f in enumerate(formats):
  format_days = days_by_format[f]
  count = len(format_days)
  ax.plot(format_days, [yticks[i + 1]] * count, \
            linewidth = 0, marker = 'o', markersize = 5, \
            alpha = dot_alpha)

fig.tight_layout()

format_str = ''
for f in sorted(formats):
  format_str += f + '_'
out_filename = 'out/images/dot/heartbeat/' + format_str \
                  + str(START_DATE.year) + '_' + str(END_DATE.year) + '.png'

Path(out_filename).parent.mkdir(exist_ok = True, parents = True)
fig.savefig(out_filename)
print("Written: " + out_filename)
