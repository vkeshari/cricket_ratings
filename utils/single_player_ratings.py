from common.data import get_daily_ratings
from common.output import readable_name_and_country, pretty_format

from datetime import date

# ['', 'batting', 'bowling', 'allrounder']
TYPE = 'batting'
# ['', 'test', 'odi', 't20']
FORMAT = 't20'

START_DATE = date(2023, 1, 1)
END_DATE = date(2024, 1, 1)

PLAYER = 'IND_Rohit_Sharma'

# ['', 'rating', 'rank', 'either', 'both']
CHANGED_DAYS_CRITERIA = 'rating'

# Alternate way to calculate allrounder ratings. Use geometric mean of batting and bowling.
ALLROUNDERS_GEOM_MEAN = True


if TYPE:
  assert TYPE in ['batting', 'bowling', 'allrounder'], "Invalid TYPE provided"
if FORMAT:
  assert FORMAT in ['test', 'odi', 't20'], "Invalid FORMAT provided"
assert START_DATE < END_DATE, "START_DATE must be earlier than END_DATE"
assert END_DATE <= date.today(), "Future END_DATE requested"

assert PLAYER, "No player provided"

assert CHANGED_DAYS_CRITERIA in ['', 'rating', 'rank', 'either', 'both'], \
        "Invalid CHANGED_DAYS_CRITERIA"


PLAYER = PLAYER + '.data'

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

  def get_player_ratings(daily_ratings, daily_ranks, player, \
                          start_date, end_date):
    if not daily_ratings or not daily_ranks:
      print ("Daily ratings or rankings are empty")
      return {}
    if not daily_ratings.keys() == daily_ranks.keys():
      print ("Key mismatch between daily ratings and ranks")
      return {}

    found = False
    for d in daily_ratings:
      if player in daily_ratings[d].keys():
        found = True
        break
    if not found:
      print("Invalid player name: " + player)
      return {}

    player_ratings = {}
    for d in daily_ratings:
      if d < start_date or d > end_date:
        continue

      if player in daily_ratings[d]:
        rating = daily_ratings[d][player]
        rank = daily_ranks[d][player]

        player_ratings[d] = {'rating': rating, 'rank': rank} 

    return player_ratings

  daily_ratings, daily_ranks = get_daily_ratings(typ, frmt, \
                                    changed_days_criteria = CHANGED_DAYS_CRITERIA, \
                                    allrounders_geom_mean = ALLROUNDERS_GEOM_MEAN)

  player_ratings = get_player_ratings(daily_ratings, daily_ranks, \
                                      PLAYER, START_DATE, END_DATE)
  print("Player ratings built for " + str(len(player_ratings)) + " days")

  if player_ratings:
    print()
    print("=== " + pretty_format(frmt, typ) + " Ratings for " \
                  + readable_name_and_country(PLAYER) + " ===")
    print("DATE\t\tRATING\tRANK")
    for d in player_ratings:
      rating = player_ratings[d]['rating']
      rank = player_ratings[d]['rank']
      print (str(d) + '\t' + '{r:3d}'.format(r = rating) + '\t' + '{r:3d}'.format(r = rank))

