from common.data import get_daily_ratings
from common.output import get_timescale_xticks, pretty_format

from datetime import date, timedelta
from pathlib import Path
from matplotlib import pyplot as plt

import math

ONE_YEAR = timedelta(days = 365)

# ['batting', 'bowling', 'allrounder']
TYPE = 'batting'
# ['test', 'odi', 't20']
FORMAT = 't20'
PLAYERS_DIR = 'players/' + TYPE + '/' + FORMAT

START_DATE = date(2007, 1, 1)
END_DATE = date(2024, 7, 1)

MAX_RATING = 1000
THRESHOLD = 0

# ['', 'rating', 'rank', 'either', 'both']
CHANGED_DAYS_CRITERIA = 'rating'

SHOW_DECADE_DATA = True
SHOW_YEAR_DATA = False
SHOW_YEAR_GRAPH = True

# Alternate way to calculate allrounder ratings. Use geometric mean of batting and bowling.
ALLROUNDERS_GEOM_MEAN = True

if TYPE:
  assert TYPE in ['', 'batting', 'bowling', 'allrounder'], "Invalid TYPE provided"
if FORMAT:
  assert FORMAT in ['', 'test', 'odi', 't20'], "Invalid FORMAT provided"
assert START_DATE < END_DATE, "START_DATE must be earlier than END_DATE"
assert END_DATE <= date.today(), "Future END_DATE requested"

assert MAX_RATING <= 1000, "MAX_RATING must not be greater than 1000"
assert THRESHOLD >= 0 and THRESHOLD < MAX_RATING, \
      "THRESHOLD must be between 0 and MAX_RATING"

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

  rating_days = sorted(daily_ratings.keys())
  total_days = len(rating_days)
  total_points = 0
  for d in rating_days:
    day_ratings = [r for r in daily_ratings[d].values() if r > 0]
    total_points += len(day_ratings)

  first_date = rating_days[0]
  last_date = rating_days[-1]
  print()
  print ("First date:\t" + str(first_date))
  print ("Last date:\t" + str(last_date))
  print()
  print ("Total days:\t{v}".format(v = total_days))
  print ("Total data points:\t{v}".format(v = total_points))


  first_decade = int(first_date.year / 10) * 10
  last_decade = int(last_date.year / 10) * 10
  days_by_decade = {d: 0 for d in range(first_decade, last_decade + 1, 10)}
  points_by_decade = {d: 0 for d in range(first_decade, last_decade + 1, 10)}

  for d in rating_days:
    decade = int(d.year / 10) * 10
    days_by_decade[decade] += 1

    day_ratings = [r for r in daily_ratings[d].values() if r > 0]
    points_by_decade[decade] += len(day_ratings)

  if SHOW_DECADE_DATA:
    print()
    print("DECADE\tDays\tData Points")
    for d in days_by_decade:
      print("{d:4d}:\t{t:4d}\t{p:6d}".format(d = d, t = days_by_decade[d], \
                                                    p = points_by_decade[d]))


  first_year = first_date.year
  last_year = last_date.year
  days_by_year = {d: 0 for d in range(first_year, last_year + 1)}
  points_by_year = {d: 0 for d in range(first_year, last_year + 1)}

  for d in rating_days:
    year = d.year
    days_by_year[year] += 1

    day_ratings = [r for r in daily_ratings[d].values() if r > 0]
    points_by_year[year] += len(day_ratings)
  
  if SHOW_YEAR_DATA:
    print()
    print("YEAR\tDays\tData Points")
    for y in days_by_year:
      print("{y:4d}:\t{t:4d}\t{p:6d}".format(y = y, t = days_by_year[y], \
                                                    p = points_by_year[y]))

  print()


  if SHOW_YEAR_GRAPH and typ == 'batting':
    if (END_DATE.year - START_DATE.year > 50):
      resolution = tuple([12.8, 7.2])
      aspect_ratio = 'widescreen'
    else:
      resolution = tuple([7.2, 7.2])
      aspect_ratio = 'square'

    fig, ax = plt.subplots(figsize = resolution)

    title = 'Number of Days of Data by year: ' + pretty_format(frmt) \
            + '\n' + str(START_DATE) + ' to ' + str(END_DATE)
    ax.set_title(title, fontsize ='xx-large')

    ax.set_xlabel('Year', fontsize ='x-large')
    ax.set_ylabel('No. of Days', fontsize ='x-large')

    ax.set_xlim(START_DATE, END_DATE)
    xticks_major, xticks_minor, xticklabels = \
            get_timescale_xticks(START_DATE, END_DATE, format = aspect_ratio)
    ax.set_xticks(xticks_major)
    ax.set_xticks(xticks_minor, minor = True)
    ax.set_xticklabels(xticklabels, fontsize ='large')

    ymax = math.ceil(max(days_by_year.values()) / 100) * 100
    ax.set_ylim(0, ymax)
    yticks = range(0, ymax, 10)
    ax.set_yticks(yticks)
    ax.set_yticklabels([str(y) for y in yticks], fontsize = 'large')

    ax.grid(True, which = 'major', axis = 'both', alpha = 0.6)
    ax.grid(True, which = 'minor', axis = 'both', alpha = 0.3)

    years, day_counts = zip(*days_by_year.items())
    dates_to_plot = [date(y, 1, 1) for y in years]
    ax.bar(dates_to_plot, day_counts, align = 'edge', width = ONE_YEAR, \
                  color = 'green', linewidth = 1, edgecolor = 'darkgrey', \
                  alpha = 0.5, label = 'No. of Days of Ratings Change')

    ax.legend(loc = 'best', fontsize = 'large')
    fig.tight_layout()

    out_filename = 'out/images/bar/datapoints/' + frmt + '_' \
                  + str(START_DATE.year) + '_' + str(END_DATE.year) + '.png'

    Path(out_filename).parent.mkdir(exist_ok = True, parents = True)
    fig.savefig(out_filename)
    print("Written: " + out_filename)
