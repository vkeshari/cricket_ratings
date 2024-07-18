from common.data import get_daily_ratings
from common.output import pretty_format, get_player_colors, readable_name_and_country

from datetime import date
from matplotlib import pyplot as plt
from pathlib import Path

# ['batting', 'bowling', 'allrounder']
TYPE = 'batting'
# ['test', 'odi', 't20']
FORMAT = 't20'

# Graph date range
GRAPH_DATE = date(2024, 7, 1)

# Upper and lower bounds of ratings to show
THRESHOLD = 500
MAX_RATING = 1000

# ['', 'rating', 'rank', 'either', 'both']
CHANGED_DAYS_CRITERIA = ''

NUM_SHOW = 20

SHOW_TABLE = True
SHOW_GRAPH = True
COLOR_BY_COUNTRY = True

# Alternate way to calculate allrounder ratings. Use geometric mean of batting and bowling.
ALLROUNDERS_GEOM_MEAN = True

if TYPE:
  assert TYPE in ['batting', 'bowling', 'allrounder'], "Invalid TYPE provided"
if FORMAT:
  assert FORMAT in ['test', 'odi', 't20'], "Invalid FORMAT provided"

assert MAX_RATING <= 1000, "MAX_RATING must not be greater than 1000"
assert THRESHOLD >= 0 and THRESHOLD < MAX_RATING, \
      "THRESHOLD must be between 0 and MAX_RATING"

assert CHANGED_DAYS_CRITERIA in ['', 'rating', 'rank', 'either', 'both']

assert NUM_SHOW >= 10 and NUM_SHOW <= 20, "NUM_SHOW should be between 10 and 20"

if COLOR_BY_COUNTRY:
  assert SHOW_GRAPH, "COLOR_BY_COUNTRY set but no SHOW_GRAPH"

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
  print (GRAPH_DATE)
  print (str(THRESHOLD) + ' : ' + str(MAX_RATING))

  daily_ratings, _ = get_daily_ratings(typ, frmt, \
                            changed_days_criteria = CHANGED_DAYS_CRITERIA, \
                            allrounders_geom_mean = ALLROUNDERS_GEOM_MEAN)

  if GRAPH_DATE in daily_ratings:

    day_ratings = daily_ratings[GRAPH_DATE]
    day_ratings = dict(sorted(day_ratings.items(),
                              key = lambda item: item[1], reverse = True))

    if SHOW_TABLE:
      print("=== TOP players (" + frmt + " " + typ + ") on " + str(GRAPH_DATE) + " ===")
      print("RANK\tRATING\tPLAYER")

      for i, p in enumerate(day_ratings):
        print (str(i + 1) + "\t" + str(day_ratings[p]) + "\t" + readable_name_and_country(p))
        if i >= NUM_SHOW - 1:
          break

    if SHOW_GRAPH:
      resolution = tuple([7.2, 7.2])
      fig, ax = plt.subplots(figsize = resolution)

      player_colors = get_player_colors(day_ratings.keys(), by_country = COLOR_BY_COUNTRY)

      players, ratings = zip(*[item for i, item in \
                                enumerate(day_ratings.items()) if i < NUM_SHOW])
      names = [readable_name_and_country(p) for p in players]
      cols = [player_colors[p] for p in players]

      title_text = "Top " + pretty_format(frmt, typ) + " by Rating" \
                    + ("(GM)" if typ == 'allrounder' and ALLROUNDERS_GEOM_MEAN else '') \
                    + "\n" + str(GRAPH_DATE)
      ax.set_title(title_text, fontsize ='xx-large')

      ax.set_ylabel('Rank', fontsize ='x-large')
      ax.set_ylim(NUM_SHOW + 0.5, 0.5)
      yticks = range(1, NUM_SHOW + 1)
      ax.set_yticks(yticks)
      ax.set_yticklabels([str(y) for y in yticks], fontsize ='large')

      ax.set_xlabel('Rating', fontsize ='x-large')
      ax.set_xlim(THRESHOLD, MAX_RATING)
      possible_xticks = range(0, 1000, 100)
      actual_xticks = [r for r in possible_xticks if r >= THRESHOLD and r <= MAX_RATING]
      ax.set_xticks(actual_xticks)
      ax.set_xticklabels([str(x) for x in actual_xticks], fontsize ='large')

      ax.grid(True, which = 'both', axis = 'x', alpha = 0.5)

      ys = [y + 1 for y in range(len(names))]

      ax.barh(ys, ratings, align = 'center', height = 0.9, \
                color = cols, alpha = 0.5)

      for i, name in enumerate(names):
        rating = ratings[i]
        plt.text(THRESHOLD + 10, i + 1, \
              s = name, \
              alpha = 1, fontsize = 'large', \
              horizontalalignment = 'left', verticalalignment = 'center')

        if rating >= THRESHOLD + (MAX_RATING - THRESHOLD) * 0.4:
          plt.text(rating + 10, i + 1, \
                    s = str(rating), \
                    alpha = 1, fontsize = 'large', \
                    horizontalalignment = 'left', verticalalignment = 'center')

      fig.tight_layout()

      out_filename = 'out/images/bar/topplayers/' + str(THRESHOLD) + '_' \
                      + str(MAX_RATING) + '_' str(NUM_SHOW) + '_' \
                      + frmt + '_' + typ \
                      + ("GEOM" if typ == 'allrounder' and ALLROUNDERS_GEOM_MEAN else '') \
                      + '_' + str(graph_date.year) + '.png'

      Path(out_filename).parent.mkdir(exist_ok = True, parents = True)
      fig.savefig(out_filename)
      print("Written: " + out_filename)
