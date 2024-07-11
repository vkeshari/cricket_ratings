from common.data import get_daily_ratings

from datetime import date

# ['batting', 'bowling', 'allrounder']
TYPE = ''
# ['test', 'odi', 't20']
FORMAT = 'odi'
PLAYERS_DIR = 'players/' + TYPE + '/' + FORMAT

START_DATE = date(1975, 1, 1)
END_DATE = date(2024, 7, 1)

MAX_RATING = 1000
THRESHOLD = 0

# ['', 'rating', 'rank', 'either', 'both']
CHANGED_DAYS_CRITERIA = 'rating'

BY_DECADE = True
BY_YEAR = False

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
  print ("Total data points:\t{v}".format(v = total_points))

  if BY_DECADE:
    first_decade = int(first_date.year / 10) * 10
    last_decade = int(last_date.year / 10) * 10
    by_decade = {d: 0 for d in range(first_decade, last_decade + 1, 10)}
    for d in rating_days:
      decade = int(d.year / 10) * 10
      day_ratings = [r for r in daily_ratings[d].values() if r > 0]
      by_decade[decade] += len(day_ratings)
    print()
    print("DECADE\tData Points")
    for d in by_decade:
      print("{d:4d}:\t{c:6d}".format(d = d, c = by_decade[d]))

  if BY_YEAR:
    first_year = first_date.year
    last_year = last_date.year
    by_year = {d: 0 for d in range(first_year, last_year + 1)}
    for d in rating_days:
      day_ratings = [r for r in daily_ratings[d].values() if r > 0]
      by_year[d.year] += len(day_ratings)
    print()
    print("YEAR\tData Points")
    for y in by_year:
      print("{y:4d}:\t{c:6d}".format(y = y, c = by_year[y]))

  print()
