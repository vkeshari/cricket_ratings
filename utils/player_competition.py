from common.data import get_daily_ratings
from common.output import readable_name_and_country, pretty_format

# ['', 'batting', 'bowling', 'allrounder']
TYPE = 'batting'
# ['', 'test', 'odi', 't20']
FORMAT = 't20'

PLAYER = 'IND_Virat_Kohli'
# ['above', 'below', 'total']
LOCATION = 'above'
NUM_SHOW = 20

# ['', 'rating', 'rank', 'either', 'both']
CHANGED_DAYS_CRITERIA = 'either'

# Alternate way to calculate allrounder ratings. Use geometric mean of batting and bowling.
ALLROUNDERS_GEOM_MEAN = True

assert TYPE in ['', 'batting', 'bowling', 'allrounder'], "Invalid TYPE provided"
assert FORMAT in ['', 'test', 'odi', 't20'], "Invalid FORMAT provided"
assert PLAYER, "No player requested"
assert LOCATION in {'above', 'below', 'total'}
assert NUM_SHOW >= 5, "NUM_SHOW must be at least 5"

player = PLAYER + '.data'


def get_player_competition(daily_ratings, player):
  competition = {}
  for d in daily_ratings:
    if player not in daily_ratings[d]:
      continue
    for p in daily_ratings[d]:
      if p not in competition:
        competition[p] = {'above': 0, 'below': 0, 'total': 0}
      if daily_ratings[d][p] >= daily_ratings[d][player]:
        competition[p]['above'] += 1
      else:
        competition[p]['below'] += 1
      competition[p]['total'] += 1
  return competition


def get_career_span(daily_ratings, player):
  player_dates = []
  for d in daily_ratings:
    if player in daily_ratings[d]:
      player_dates.append(d)
  player_dates = sorted(player_dates)

  return min(player_dates), max(player_dates)


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

  daily_ratings, _ = get_daily_ratings(typ, frmt, \
                            changed_days_criteria = CHANGED_DAYS_CRITERIA, \
                            allrounders_geom_mean = ALLROUNDERS_GEOM_MEAN)

  first_date, last_date = get_career_span(daily_ratings, player)
  competition = get_player_competition(daily_ratings, player)
  competition = dict(sorted(competition.items(), \
                            key = lambda item: item[1][LOCATION], reverse = True))

  print()
  print("=== " + pretty_format(frmt, typ) \
                + " competition for " + readable_name_and_country(player) + " ===")
  print (str(first_date) + " to " + str(last_date))
  print ("No.\tABOVE\tBELOW\tTOTAL\tPLAYER")
  for i, p in enumerate(competition):
    print("{r:2d}\t{a:4d}\t{b:4d}\t{t:4d}\t".format(r = i, \
                      a = competition[p]['above'], b = competition[p]['below'], \
                      t = competition[p]['total']) \
                + readable_name_and_country(p))
    if i == NUM_SHOW:
      break
