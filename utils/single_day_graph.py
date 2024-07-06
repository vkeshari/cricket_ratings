from common.data import get_daily_ratings
from common.output import get_player_colors, readable_name_and_country

from datetime import date
from matplotlib import pyplot as plt, cm

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

assert TYPE in ['batting', 'bowling', 'allrounder'], "Invalid TYPE provided"
assert FORMAT in ['test', 'odi', 't20'], "Invalid FORMAT provided"

assert MAX_RATING <= 1000, "MAX_RATING must not be greater than 1000"
assert THRESHOLD >= 0 and THRESHOLD < MAX_RATING, \
      "THRESHOLD must be between 0 and MAX_RATING"

assert CHANGED_DAYS_CRITERIA in ['', 'rating', 'rank', 'either', 'both']

assert NUM_SHOW >= 10 and NUM_SHOW <= 25, "NUM_SHOW should be between 10 and 25"

print (FORMAT + '\t' + TYPE)
print (GRAPH_DATE)
print (str(THRESHOLD) + ' : ' + str(MAX_RATING))

daily_ratings, _ = get_daily_ratings(TYPE, FORMAT, \
                          changed_days_criteria = CHANGED_DAYS_CRITERIA, \
                          allrounders_geom_mean = ALLROUNDERS_GEOM_MEAN)

if GRAPH_DATE in daily_ratings:

  day_ratings = daily_ratings[GRAPH_DATE]
  day_ratings = dict(sorted(day_ratings.items(),
                            key = lambda item: item[1], reverse = True))

  if SHOW_TABLE:
    print("=== TOP players (" + FORMAT + " " + TYPE + ") on " + str(GRAPH_DATE) + " ===")
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

    title_text = "Top " + FORMAT + " " + TYPE + " players by rating on " + str(GRAPH_DATE)
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

    ax.grid(True, which='both', axis='x', alpha=0.5)

    ys = [y + 1 for y in range(len(names))]

    ax.barh(ys, ratings, align='center', height=0.9, \
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
    plt.show()