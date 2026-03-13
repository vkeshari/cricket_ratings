from common.data import get_daily_ratings
from common.output import get_player_colors, get_timescale_xticks, readable_name_and_country, \
                          pretty_format

from datetime import date, timedelta
from matplotlib import pyplot as plt
from pathlib import Path

ONE_DAY = timedelta(days = 1)

# ['', 'batting', 'bowling', 'allrounder']
TYPE = 'batting'
# ['', 'test', 'odi', 't20']
FORMAT = 't20'

START_DATE = date(2026, 1, 1)
END_DATE = date(2026, 3, 1)

MAX_RATING = 1000
THRESHOLD = 700
Y_BUFFER = 100

COLOR_BY_COUNTRY = True
SHOW_NAMES = True

# Alternate way to calculate allrounder ratings. Use geometric mean of batting and bowling.
ALLROUNDERS_GEOM_MEAN = True


if TYPE:
  assert TYPE in ['batting', 'bowling', 'allrounder'], "Invalid TYPE provided"
if FORMAT:
  assert FORMAT in ['test', 'odi', 't20'], "Invalid FORMAT provided"
assert START_DATE < END_DATE, "START_DATE must be earlier than END_DATE"
assert END_DATE <= date.today(), "Future END_DATE requested"

assert MAX_RATING <= 1000, "MAX_RATING must not be greater than 1000"
assert THRESHOLD >= 100 and THRESHOLD < MAX_RATING, \
      "THRESHOLD must be between 100 and MAX_RATING"
assert 0 <= Y_BUFFER <= 100, "Y_BUFFER must be between 0 and 100"

DATA_THRESHOLD = THRESHOLD - Y_BUFFER


def get_filtered_stats(daily_ratings, min_rating, start_date, end_date):
  assert start_date in daily_ratings, "START_DATE not found in ratings"
  start_date_ratings = {p: r for p, r in daily_ratings[start_date].items() if r >= DATA_THRESHOLD}

  assert end_date in daily_ratings, "END_DATE not found in ratings"
  end_date_ratings = {p: r for p, r in daily_ratings[end_date].items() if r >= DATA_THRESHOLD}

  filtered_players = set()
  for d in daily_ratings:
    if d < start_date or d > end_date:
      continue

    for p in daily_ratings[d]:
      if daily_ratings[d][p] >= min_rating:
        if p not in filtered_players:
          filtered_players.add(p)

  filtered_ratings = {p : {} for p in filtered_players}
  for p in filtered_ratings:
    filtered_ratings[p] = {d: daily_ratings[d][p] for d in daily_ratings \
                            if start_date <= d <= end_date and p in daily_ratings[d]}
  
  return filtered_ratings, start_date_ratings, end_date_ratings


types_and_formats = []
if TYPE and FORMAT:
  types_and_formats.append((TYPE, FORMAT))
elif TYPE:
  for f in ['test', 'odi', 't20']:
    types_and_formats.append((TYPE, f))
elif FORMAT:
  for t in ['batting', 'bowling']: # No 'allrounder' because of different THRESHOLD
    types_and_formats.append((t, FORMAT))
else:
  for f in ['test', 'odi', 't20']:
    for t in ['batting', 'bowling']:
      types_and_formats.append((t, f))

for typ, frmt in types_and_formats:
  print (frmt + ' : ' + typ)
  print (str(START_DATE) + ' : ' + str(END_DATE))

  daily_ratings, _ = get_daily_ratings(typ, frmt, changed_days_criteria = '', \
                          allrounders_geom_mean = ALLROUNDERS_GEOM_MEAN)

  filtered_ratings, start_date_ratings, end_date_ratings = \
            get_filtered_stats(daily_ratings, DATA_THRESHOLD, START_DATE, END_DATE)
  print("Filtered stats built with " + str(len(filtered_ratings)) + " keys")

  if filtered_ratings:
    resolution = tuple([12.8, 7.2])
    fig, ax = plt.subplots(figsize = resolution)

    ax.set_title("Ratings of top " + pretty_format(frmt, typ) \
                      +("(GEOM)" if typ == 'allrounder' \
                                and ALLROUNDERS_GEOM_MEAN else '') \
                      + "\n" + str(START_DATE) + " to " + str(END_DATE), \
                  fontsize ='xx-large')

    ax.set_ylabel("Rating", fontsize = 'x-large')
    ax.set_ylim(THRESHOLD, MAX_RATING)
    yticks = range(THRESHOLD, MAX_RATING + 1, 50)
    ax.set_yticks(yticks)
    ax.set_yticklabels([str(y) for y in yticks], fontsize ='large')

    if SHOW_NAMES:
      x_buffer = timedelta(days = ((END_DATE - START_DATE) / 3).days + 1)
    else:
      x_buffer = 0
    graph_start_date = START_DATE - x_buffer
    graph_end_date = END_DATE + x_buffer

    ax.set_xlabel("Date", fontsize = 'x-large')
    ax.set_xlim(graph_start_date, graph_end_date)
    xticks_major, xticks_minor, xticklabels = \
            get_timescale_xticks(graph_start_date, graph_end_date, format = 'widescreen')
    ax.set_xticks(xticks_major)
    ax.set_xticks(xticks_minor, minor = True)
    ax.set_xticklabels(xticklabels, fontsize ='large')
    
    ax.grid(True, which = 'major', axis = 'both', alpha = 0.6)
    ax.grid(True, which = 'minor', axis = 'both', alpha = 0.3)

    player_to_color = get_player_colors(filtered_ratings.keys(), by_country = COLOR_BY_COUNTRY)

    for p in filtered_ratings:
      (xs, ys) = zip(*filtered_ratings[p].items())

      ax.plot(xs, ys, linestyle = '-', linewidth = 5, antialiased = True, \
                        alpha = 0.3, color = player_to_color[p], \
                        label = readable_name_and_country(p))
      
    xs = [START_DATE] * len(start_date_ratings)
    names, ys = zip(*start_date_ratings.items())
    cols = [player_to_color[n] for n in names]
    ax.scatter(xs, ys, s = 50, c = cols, edgecolors = 'none', linewidths = 0, marker = 'o',
                antialiased = True, alpha = 0.5)
    
    xs = [END_DATE] * len(end_date_ratings)
    names, ys = zip(*end_date_ratings.items())
    cols = [player_to_color[n] for n in names]
    ax.scatter(xs, ys, s = 50, c = cols, edgecolors = 'none', linewidths = 0, marker = 'o',
                antialiased = True, alpha = 0.5)

    if SHOW_NAMES:
      for p in start_date_ratings:
        if start_date_ratings[p] < THRESHOLD:
          continue
        ax.text(x = START_DATE - ONE_DAY, y = start_date_ratings[p],
                  s = str(readable_name_and_country(p)),
        alpha = 0.8, fontsize = 'medium', antialiased = True,
        horizontalalignment = 'right', verticalalignment = 'center')

      for p in end_date_ratings:
        if end_date_ratings[p] < THRESHOLD:
          continue
        ax.text(x = END_DATE + ONE_DAY, y = end_date_ratings[p],
                  s = str(readable_name_and_country(p)),
        alpha = 0.8, fontsize = 'medium', antialiased = True,
        horizontalalignment = 'left', verticalalignment = 'center')

    fig.tight_layout()

    out_filename = 'out/images/line/interval/' \
                    + frmt + '_' + typ \
                    + ("GEOM" if typ == 'allrounder' and ALLROUNDERS_GEOM_MEAN else '') \
                    + '_' + str(THRESHOLD) \
                    + '_' + str(START_DATE.year) + '_' + str(END_DATE.year) + '.png'

    Path(out_filename).parent.mkdir(exist_ok = True, parents = True)
    fig.savefig(out_filename)
    print("Written: " + out_filename)
