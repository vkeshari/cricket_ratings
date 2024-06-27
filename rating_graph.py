import math

from datetime import date, timedelta, datetime
from os import listdir
from scipy import interpolate

ONE_DAY = timedelta(days = 1)
ONE_MONTH = timedelta(days = 30)
ONE_YEAR = timedelta(days = 365)

MAX_RATING = 1000

# ['batting', 'bowling', 'allrounder']
TYPE = 'batting'
# ['test', 'odi', 't20']
FORMAT = 't20'
# ['line', 'bar']
GRAPH_TYPE = 'bar'
GRAPH_SMOOTH = True

# Empty or country code
COUNTRY_PREFIX = ''

# Graph date range
START_DATE = date(2021, 1, 1)
END_DATE = date(2024, 1, 1)

# Upper and lower bounds of ratings to show
THRESHOLD = 500
Y_BUFFER = 50
WORKING_THRESHOLD = THRESHOLD - Y_BUFFER

# bar graph only
TOP_PLAYERS = 10
MIN_RATING_SCALE = 500

# line graph only
DATE_POSITION = MAX_RATING - 20

NUM_YEARS_TO_SHOW = 1
GRAPH_HISTORY = ONE_YEAR * NUM_YEARS_TO_SHOW

# Alternate way to calculate allrounder ratings. Use geometric mean of batting and bowling.
ALLROUNDERS_GEOM_MEAN = False

assert TYPE in ['batting', 'bowling', 'allrounder'], "Invalid TYPE provided"
assert FORMAT in ['test', 'odi', 't20'], "Invalid FORMAT provided"
assert START_DATE < END_DATE, "START_DATE must be earlier than END_DATE"
assert END_DATE <= date.today(), "Future END_DATE requested"

assert GRAPH_TYPE in ['line', 'bar'], "Invalid GRAPH_TYPE requested"
assert MAX_RATING <= 1000, "MAX_RATING must not be greater than 1000"
assert TOP_PLAYERS >= 10 and TOP_PLAYERS <= 40, "TOP_PLAYERS must be between 10 and 40"
assert THRESHOLD >= 0, "THRESHOLD must not be negative"
assert MIN_RATING_SCALE >= 0, "MIN_RATING_SCALE must not be negative"
assert MIN_RATING_SCALE <= THRESHOLD, "THRESHOLD cannot be less than MIN_RATING_SCALE"

assert DATE_POSITION < MAX_RATING and DATE_POSITION > THRESHOLD, \
    "DATE_POSITION outside range"
assert NUM_YEARS_TO_SHOW >= 1 and NUM_YEARS_TO_SHOW <= 5, \
            "NUM_YEARS_TO_SHOW must be between 1 and 5 years"

def string_to_date(s):
  dt = datetime.strptime(s, '%Y%m%d')
  return date(dt.year, dt.month, dt.day)

def get_player_ratings(typ, frmt, threshold, smooth = False):
  player_ratings = {}
  max_ratings = {}
  player_files = listdir('players/' + typ + '/' + frmt)
  for p in player_files:
    if len(COUNTRY_PREFIX) > 0 and not p.startswith(COUNTRY_PREFIX + '_'):
      continue

    lines = []
    with open('players/' + typ + '/' + frmt + '/' + p, 'r') as f:
      lines += f.readlines()

    min_player_date = string_to_date(lines[0].split(',')[0])
    max_player_date = string_to_date(lines[-1].split(',')[0])

    # Get all ratings for a player
    full_player_ratings = {}
    for i, l in enumerate(lines):
      parts = l.split(',')
      d = string_to_date(parts[0])

      rating = eval(parts[2])
      if typ == 'allrounder' and ALLROUNDERS_GEOM_MEAN:
        rating = int(math.sqrt(rating * 1000))
      full_player_ratings[d] = rating

    # Remove redundant middle points
    trimmed_player_ratings = {}
    for d in full_player_ratings:
      if d - ONE_DAY in full_player_ratings \
          and d + ONE_DAY in full_player_ratings \
          and full_player_ratings[d] == full_player_ratings[d - ONE_DAY]:
        continue
      trimmed_player_ratings[d] = full_player_ratings[d]

    if smooth and len(trimmed_player_ratings) > 1:
      (ds, rs) = list(zip(*sorted(trimmed_player_ratings.items())))
      ts = [(d - min_player_date).days for d in ds]
      all_dates_range = range((max_player_date - min_player_date).days + 1)

      interpolated_ratings = interpolate.pchip_interpolate(ts, rs, all_dates_range)
      trimmed_player_ratings = {min_player_date + timedelta(days = t): r \
                                for (t, r) in zip(all_dates_range, interpolated_ratings)}

    first_date = max(min_player_date, START_DATE)
    last_date = min(max_player_date, END_DATE)

    # Build ratings for date range
    player_ratings[p] = {}
    player_ratings[p]['all_ratings'] = {}
    max_rating = 0
    for d in trimmed_player_ratings:
      if d < first_date or d > last_date:
        continue
      rating = trimmed_player_ratings[d]
      if rating <= threshold:
        continue
      if int(rating) > max_rating:
        max_rating = int(rating)

      player_ratings[p]['all_ratings'][d] = rating

      if d not in max_ratings \
            or rating > max_ratings[d]['rating']:
        max_ratings[d] = {'rating': rating, 'date': d, 'name': p}

    player_ratings[p]['max_rating'] = max_rating

    if len(player_ratings[p]['all_ratings']) == 0:
      del player_ratings[p]
      continue

    # Fill missing dates with last available rating
    last_rating = 0
    d = first_date
    while d <= last_date:
      if d not in player_ratings[p]['all_ratings']:
        player_ratings[p]['all_ratings'][d] = last_rating
      last_rating = player_ratings[p]['all_ratings'][d]
      if last_rating <= threshold:
        last_rating = 0
      d += ONE_DAY

    player_ratings[p]['first_date'] = first_date
    player_ratings[p]['last_date'] = last_date

    print (str(len(player_ratings)) + '\t' + typ + '\t' \
            + str(len(player_ratings[p]['all_ratings'])) + '\t' \
            + 'Max: ' + str(player_ratings[p]['max_rating']) + '\t' + p)

  max_ever_ratings = {}
  max_ever_ratings[START_DATE - ONE_DAY] = {'rating': 0, \
                                            'date' : START_DATE - ONE_DAY, \
                                            'name' : 'Sunil Shetty'}
  d = START_DATE
  while d <= END_DATE:
    if d in max_ratings and \
          max_ratings[d]['rating'] > max_ever_ratings[d - ONE_DAY]['rating']:
      max_ever_ratings[d] = max_ratings[d]
    else:
      max_ever_ratings[d] = max_ever_ratings[d - ONE_DAY]
    d += ONE_DAY

  return (player_ratings, max_ever_ratings)

(player_ratings, max_ever_ratings) = get_player_ratings(TYPE, FORMAT, WORKING_THRESHOLD,
                                                        smooth = GRAPH_SMOOTH)

def get_dates_to_plot():
  dates_to_plot = []
  d = START_DATE
  while d <= END_DATE:
    dates_to_plot.append(d)
    d += ONE_DAY
  return dates_to_plot
dates_to_plot = get_dates_to_plot()

time_series = {}
for d in dates_to_plot:
  time_series[d] = {}

for p in player_ratings:
  d = player_ratings[p]['first_date']
  while d <= player_ratings[p]['last_date']:
    time_series[d][p] = player_ratings[p]['all_ratings'][d]
    d += ONE_DAY

from matplotlib import pyplot, cm, animation

def readable_name(p):
  sep = p.find('_')
  return p[sep+1:].split('.')[0].replace('_', ' ')

def country(p):
  return p.split('_')[0]

def full_readable_name(p):
  return readable_name(p) + ' (' + country(p) + ')'

def get_player_colors(player_ratings):
  player_colors = {}
  color_stops = []
  for i in range(len(player_ratings)):
    color_stops.append(i / len(player_ratings))
  colors = cm.rainbow(color_stops)
  player_colors = {}
  i = 0
  for p in player_ratings:
    player_colors[p] = colors[i]
    i += 1
  return player_colors
player_colors = get_player_colors(player_ratings)

def get_country_colors():
  country_colors = {}
  country_colors['AFG'] = 'dodgerblue'
  country_colors['AUS'] = 'yellow'
  country_colors['BAN'] = 'forestgreen'
  country_colors['BRM'] = 'rosybrown'
  country_colors['CAN'] = 'crimson'
  country_colors['EAF'] = 'goldenrod'
  country_colors['ENG'] = 'cornflowerblue'
  country_colors['HK'] = 'red'
  country_colors['IND'] = 'blue'
  country_colors['IRE'] = 'limegreen'
  country_colors['KEN'] = 'darkgreen'
  country_colors['NAM'] = 'steelblue'
  country_colors['NED'] = 'darkorange'
  country_colors['NZ'] = 'black'
  country_colors['PAK'] = 'green'
  country_colors['SA'] = 'lime'
  country_colors['SCO'] = 'royalblue'
  country_colors['SL'] = 'darkblue'
  country_colors['UAE'] = 'dimgrey'
  country_colors['WI'] = 'maroon'
  country_colors['ZIM'] = 'orangered'
  return country_colors
country_colors = get_country_colors()

player_to_color = {}
for p in player_ratings:
  if len(COUNTRY_PREFIX) > 0:
    player_to_color[p] = player_colors[p]
  elif country(p) in country_colors:
    player_to_color[p] = country_colors[country(p)]
  else:
    player_to_color[p] = 'lightgrey'

def draw_for_date(current_date):
  if current_date.day == 1:
    print (current_date)
  axs.clear()

  type_title_string = ''
  if TYPE == 'batting':
    type_title_string = 'Batsmen'
  if TYPE == 'bowling':
    type_title_string = 'Bowlers'
  if TYPE == 'allrounder':
    type_title_string = 'All-Rounders'

  format_title_string = ''
  if FORMAT == 'test':
    format_title_string = 'Test'
  if FORMAT == 'odi':
    format_title_string = 'ODI'
  if FORMAT == 't20':
    format_title_string = 'T20I'

  country_title_prefix = ''
  if COUNTRY_PREFIX:
    country_title_prefix = ' ' + COUNTRY_PREFIX

  title_text = 'Top' + country_title_prefix + ' ' + format_title_string \
                  + ' ' + type_title_string + ' Rating: ' \
                  + '(Minimum Rating: ' + str(THRESHOLD) + ')\n' \
                  + str(START_DATE) + ' to ' + str(END_DATE) \

  if GRAPH_TYPE == 'bar':
    axs.set_title(title_text, fontsize ='xx-large')

    axs.set_ylabel('Rank', fontsize ='xx-large')
    axs.set_ylim(TOP_PLAYERS, 0)
    yticks = range(1, TOP_PLAYERS + 1)
    axs.set_yticks(yticks)
    axs.set_yticklabels([str(y) for y in yticks], fontsize ='x-large')

    axs.set_xlabel('Rating', fontsize ='xx-large')
    axs.set_xlim(MIN_RATING_SCALE, MAX_RATING)
    possible_xticks = range(0, 1000, 100)
    actual_xticks = [r for r in possible_xticks if r >= MIN_RATING_SCALE and r <= MAX_RATING]
    axs.set_xticks(actual_xticks)
    axs.set_xticklabels([str(x) for x in actual_xticks], fontsize ='x-large')

    axs.grid(True, which='both', axis='x', alpha=0.5)

    players_for_date = [item for item in time_series[current_date].items() \
                          if item[1] > THRESHOLD]
    ps = []
    rs = []
    if players_for_date:
      (ps, rs) = list(zip(*sorted(players_for_date, \
                            key = lambda item: item[1], reverse = True) \
                          [: TOP_PLAYERS]))

    names = [full_readable_name(p) for p in ps]
    cols = [player_to_color[p] for p in ps]
    ys = [y + 0.5 for y in range(len(names))]

    axs.barh(ys, rs, align='center', height=0.9, \
              color = cols, alpha = 0.6)

    for i, name in enumerate(names):
      pyplot.text(MIN_RATING_SCALE + 10, i + 0.5, \
            s = name, \
            alpha=1, fontsize='x-large', \
            horizontalalignment='left', verticalalignment='center')

    pyplot.text(MAX_RATING, TOP_PLAYERS, \
                s = str(current_date), \
                alpha=1, fontsize='xx-large', \
                horizontalalignment='right', verticalalignment='bottom')

    max_ever_rating = max_ever_ratings[current_date]['rating']
    max_ever_rating_date = max_ever_ratings[current_date]['date']
    max_ever_rating_name = max_ever_ratings[current_date]['name']
    pyplot.axvline(x = max_ever_rating, color="grey", linestyle=":")

    max_ever_rating_text = ' Best: ' + str(int(max_ever_rating)) + '\n' \
                            + '  ' + str(max_ever_rating_date) + '\n' \
                            + '  ' + readable_name(max_ever_rating_name) + '\n' \
                            + '   ' + '(' + country(max_ever_rating_name) + ')'
    
    if max_ever_rating > (MIN_RATING_SCALE + (MAX_RATING - MIN_RATING_SCALE) / 2):
      pyplot.text(max_ever_rating, 0.5, \
                  s = max_ever_rating_text, \
                  alpha=1, fontsize='medium', \
                  horizontalalignment='left', verticalalignment='top')

  elif GRAPH_TYPE == 'line':
    axs.set_title(title_text, fontsize ='x-large')

    possible_yticks = range(0, 1000, 100)
    possible_xticks = [date(year = y, month = 1, day = 1) \
                        for y in range(START_DATE.year, END_DATE.year + 1)]

    axs.set_ylabel('Rating', fontsize ='large')
    axs.set_ylim(THRESHOLD, MAX_RATING)
    actual_yticks = [t for t in possible_yticks if t > THRESHOLD and t < MAX_RATING]
    axs.set_yticks(actual_yticks)

    axs.set_xlabel('Date', fontsize ='large')
    graph_start_date = current_date - GRAPH_HISTORY
    axs.set_xlim(graph_start_date, current_date + ONE_YEAR)
    actual_xticks = [d for d in possible_xticks \
                      if d >= graph_start_date and d <= current_date]
    axs.set_xticks(actual_xticks)
    axs.set_xticklabels([str(d.year) for d in actual_xticks])

    axs.grid(True, which = 'both', axis = 'both', alpha = 0.5)

    for p in player_ratings:
      dates_to_plot = []
      ratings_to_plot = []
      for (d, r) in sorted(player_ratings[p]['all_ratings'].items()):
        if d >= graph_start_date and d <= current_date:
          dates_to_plot.append(d)
          ratings_to_plot.append(r)

      pyplot.plot(dates_to_plot, ratings_to_plot, \
                  linewidth = 5, antialiased = True, alpha = 0.5, \
                  color = player_to_color[p])

    for p in time_series[current_date]:
      if time_series[current_date][p] < THRESHOLD:
        continue

      pyplot.plot(current_date, time_series[current_date][p], \
                  marker = "o", markersize = 5, \
                  color = player_to_color[p])

      pyplot.text(current_date + ONE_MONTH, time_series[current_date][p], \
                  s = full_readable_name(p), \
                  alpha = 0.5, fontsize = 'medium', \
                  horizontalalignment = 'left', verticalalignment = 'center')

    pyplot.text(current_date - GRAPH_HISTORY + ONE_MONTH, DATE_POSITION, \
                s = str(current_date), \
                alpha = 1, fontsize = 'large', \
                horizontalalignment = 'left', verticalalignment = 'top')

    max_ever_rating = max_ever_ratings[current_date]['rating']
    max_ever_rating_date = max_ever_ratings[current_date]['date']
    max_ever_rating_name = max_ever_ratings[current_date]['name']
    max_line_xmax = GRAPH_HISTORY.days / (GRAPH_HISTORY + ONE_YEAR).days
    pyplot.axhline(y = max_ever_rating, xmax = max_line_xmax, \
                    color = "grey", linestyle = ":")

    max_ever_rating_text = ' Best: ' + str(int(max_ever_rating)) \
                            + ' on ' + str(max_ever_rating_date) \
                            + ', ' + full_readable_name(max_ever_rating_name)
    
    pyplot.text(current_date - GRAPH_HISTORY + ONE_MONTH, max_ever_rating + 5, \
                s = max_ever_rating_text, \
                alpha = 0.5, fontsize = 'medium', \
                horizontalalignment = 'left', verticalalignment = 'bottom')

  pyplot.draw()

FILE_NAME = 'out/'
if len(COUNTRY_PREFIX) > 0:
  FILE_NAME += COUNTRY_PREFIX
else:
  FILE_NAME += 'ALL'
FILE_NAME += '_' + str(START_DATE.year) + '_' + str(END_DATE.year) \
              + '_' + TYPE + '_' + FORMAT + '_' + str(THRESHOLD) \
              + '_' + GRAPH_TYPE + '_' + str(GRAPH_SMOOTH) + '.mp4'

if GRAPH_TYPE == 'line':
  if NUM_YEARS_TO_SHOW > 2:
    resolution = (12.8, 7.2)
  else:
    resolution = (7.2, 7.2)
elif GRAPH_TYPE == 'bar':
  if TOP_PLAYERS > 15:
    resolution = (7.2, 12.8)
  else:
    resolution = (7.2, 7.2)

fig, axs = pyplot.subplots(figsize = resolution)

print ('Writing:' + '\t' + FILE_NAME)
writer = animation.FFMpegWriter(fps = 60, bitrate = 5000)
with writer.saving(fig, FILE_NAME, dpi = 100):
  for current_date in dates_to_plot:
    draw_for_date(current_date)
    writer.grab_frame()
print ('Done:' + '\t' + FILE_NAME)

