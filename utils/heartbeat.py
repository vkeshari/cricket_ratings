from common.data import get_daily_ratings
from common.output import get_timescale_xticks, pretty_format, resolution_by_span

from datetime import date
from pathlib import Path
from matplotlib import pyplot as plt

import numpy as np

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

types_and_formats = []
for f in ['t20', 'odi', 'test']:
  for t in ['batting', 'bowling']:
    types_and_formats.append((t, f))

days_by_ft = {}
for typ, frmt in types_and_formats:
  print (frmt + ' : ' + typ)
  print (str(START_DATE) + ' : ' + str(END_DATE))

  daily_ratings, _ = get_daily_ratings(typ, frmt, \
                            changed_days_criteria = CHANGED_DAYS_CRITERIA, \
                            allrounders_geom_mean = ALLROUNDERS_GEOM_MEAN)

  rating_days = [d for d in sorted(daily_ratings.keys()) \
                  if d >= START_DATE and d <= END_DATE]
  days_by_ft[(frmt, typ)] = rating_days

all_ft = [pretty_format(ft[0], ft[1]) for ft in days_by_ft.keys()]

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
yticks = np.linspace(0, ymax, len(all_ft) + 2)
ax.set_yticks(yticks)
ax.set_yticklabels([''] + all_ft + [''], fontsize = 'large')

ax.grid(True, which = 'major', axis = 'both', alpha = 0.6)
ax.grid(True, which = 'minor', axis = 'both', alpha = 0.3)

for i, (f, t) in enumerate(days_by_ft.keys()):
  ft_days = days_by_ft[(f, t)]
  count = len(ft_days)
  ax.plot(ft_days, [yticks[i + 1]] * count, \
            linewidth = 0, marker = 'o', markersize = 5, \
            alpha = 0.1)

fig.tight_layout()

out_filename = 'out/images/dot/heartbeat/' \
                  + str(START_DATE.year) + '_' + str(END_DATE.year) + '.png'

Path(out_filename).parent.mkdir(exist_ok = True, parents = True)
fig.savefig(out_filename)
print("Written: " + out_filename)
