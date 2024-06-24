from datetime import date, timedelta, datetime
from os import listdir
from scipy import interpolate

# ['batting', 'bowling', 'allrounder']
TYPE = 'batting'
# ['test', 'odi', 't20']
FORMAT = 't20'
# ['line', 'bar']
GRAPH_TYPE = ''
GRAPH_SMOOTH = True

# empty or country code
COUNTRY_PREFIX = ''

THRESHOLD = 700
Y_BUFFER = 50
WORKING_THRESHOLD = THRESHOLD - Y_BUFFER
MAX_RATING = 1000

TITLE_POSITION = 900

# between available data range
START_DATE = date(2021, 1, 1)
END_DATE = date(2024, 1, 1)

ONE_DAY = timedelta(days=1)
ONE_WEEK = timedelta(days=7)
ONE_MONTH = timedelta(days=30)
ONE_YEAR = timedelta(days=365)

NUM_DAYS_TO_SHOW = 365 * 5
GRAPH_HISTORY = ONE_DAY * NUM_DAYS_TO_SHOW

def date_to_parts(d):
  yr = str(d.year)
  mn = str(d.month)
  if (d.month < 10):
    mn = '0' + mn
  dy = str(d.day)
  if (d.day < 10):
    dy = '0' + dy
  return (yr, mn, dy)

def string_to_date(s):
  dt = datetime.strptime(s, '%Y%m%d')
  return date(dt.year, dt.month, dt.day)

def get_player_ratings(typ, frmt, threshold, smooth = False):
  player_ratings = {}
  player_files = listdir('players/' + typ + '/' + frmt)
  for p in player_files:
    if len(COUNTRY_PREFIX) > 0 and not p.startswith(COUNTRY_PREFIX + '_'):
      continue

    lines = []
    with open('players/' + typ + '/' + frmt + '/' + p, 'r') as f:
      lines += f.readlines()

    min_player_date = string_to_date(lines[0].split(',')[0])
    max_player_date = string_to_date(lines[-1].split(',')[0])

    full_player_ratings = {}
    last_rating = -1
    for i, l in enumerate(lines):
      parts = l.split(',')
      d = string_to_date(parts[0])
      rating = eval(parts[2])
      if rating == last_rating and i < len(lines) - 1:
        continue
      last_rating = rating
      full_player_ratings[d] = rating

    if smooth and len(full_player_ratings) > 3:
      (ds, rs) = list(zip(*sorted(full_player_ratings.items())))
      ts = [(d - min_player_date).days for d in ds]
      all_dates_range = range((max_player_date - min_player_date).days + 1)

      interpolated_ratings = interpolate.pchip_interpolate(ts, rs, all_dates_range)
      full_player_ratings = {min_player_date + timedelta(days = t): r for (t, r) in zip(all_dates_range, interpolated_ratings)}

    first_date = max(min_player_date, START_DATE)
    last_date = min(max_player_date, END_DATE)

    player_ratings[p] = {}
    player_ratings[p]['all_ratings'] = {}
    player_ratings[p]['max_ratings'] = {}
    max_rating = 0
    for d in full_player_ratings:
      if d < first_date or d > last_date:
        continue
      rating = full_player_ratings[d]
      if rating <= threshold:
        continue
      if int(rating) > max_rating:
        max_rating = int(rating)
        player_ratings[p]['max_ratings'][d] = max_rating
      player_ratings[p]['all_ratings'][d] = rating

    if len(player_ratings[p]['all_ratings']) == 0:
      del player_ratings[p]
      continue

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
            + 'Max: ' + str(max(player_ratings[p]['max_ratings'].values())) + '\t' + p)
  return player_ratings

player_ratings = get_player_ratings(TYPE, FORMAT, WORKING_THRESHOLD, smooth = GRAPH_SMOOTH)

time_series = {}
d = START_DATE
while d <= END_DATE:
  time_series[d] = {}
  d += ONE_DAY

for p in player_ratings:
  d = player_ratings[p]['first_date']
  while d <= player_ratings[p]['last_date']:
    time_series[d][p] = player_ratings[p]['all_ratings'][d]
    d += ONE_DAY

from matplotlib import pyplot, axes, cm, animation

def readable_name(n):
  sep = n.find('_')
  return n[sep+1:].split('.')[0].replace('_', ' ')

def country(n):
  return n.split('_')[0]

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

player_colors = {}
country_colors = {}
if len(COUNTRY_PREFIX) > 0:
  player_colors = get_player_colors(player_ratings)
else:
  country_colors = get_country_colors()

POSSIBLE_YTICKS = range(0, 1000, 100)
POSSIBLE_XTICKS = [date(year = y, month = 1, day = 1) \
                    for y in range(START_DATE.year, END_DATE.year + 1)]

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

  axs.set_title(COUNTRY_PREFIX + ' ' + format_title_string \
                + ' ' + type_title_string + ' Rating : ' \
                + str(START_DATE) + ' to ' + str(END_DATE) \
                + '\n(Min. Rating: ' + str(THRESHOLD) + ')')

  axs.set_ylabel('Rating')
  axs.set_ylim(THRESHOLD, MAX_RATING)
  actual_yticks = [t for t in POSSIBLE_YTICKS if t > THRESHOLD and t < MAX_RATING]
  axs.set_yticks(actual_yticks)

  axs.set_xlabel('Date')
  graph_start_date = current_date - GRAPH_HISTORY
  axs.set_xlim(graph_start_date, current_date + ONE_YEAR)
  actual_xticks = [d for d in POSSIBLE_XTICKS \
                    if d >= graph_start_date and d <= current_date]
  axs.set_xticks(actual_xticks)
  axs.set_xticklabels([str(d.year) for d in actual_xticks])
  axs.grid(True, which='both', axis='both', alpha=0.5)

  for p in player_ratings.keys():
    if len(COUNTRY_PREFIX) > 0:
      player_color = player_colors[p]
    elif country(p) in country_colors:
      player_color = country_colors[country(p)]
    else:
      player_color = 'black'

    dates_to_plot = []
    ratings_to_plot = []
    for (d, r) in sorted(player_ratings[p]['all_ratings'].items()):
      if d >= graph_start_date and d <= current_date:
        dates_to_plot.append(d)
        ratings_to_plot.append(r)

    pyplot.plot(dates_to_plot, ratings_to_plot, \
                linewidth=5, antialiased=True, alpha=0.5, \
                color=player_color)

  for p in time_series[current_date]:
    if time_series[current_date][p] < THRESHOLD:
      continue
    if len(COUNTRY_PREFIX) > 0:
      player_color = player_colors[p]
    elif country(p) in country_colors:
      player_color = country_colors[country(p)]
    else:
      player_color = 'black'

    pyplot.plot(current_date, time_series[current_date][p], \
                marker="o", markersize=5, \
                color=player_color)

    pyplot.text(current_date + ONE_MONTH, time_series[current_date][p], \
                s=readable_name(p) + ' (' + country(p) + ')', \
                alpha=0.5, fontsize='medium', \
                horizontalalignment='left', verticalalignment='center')

  pyplot.text(current_date - GRAPH_HISTORY + ONE_MONTH, TITLE_POSITION, \
              s=str(current_date), \
              alpha=1, fontsize='large', \
              horizontalalignment='left', verticalalignment='bottom')

  pyplot.draw()

FILE_NAME = 'out/'
if len(COUNTRY_PREFIX) > 0:
  FILE_NAME += COUNTRY_PREFIX
else:
  FILE_NAME += 'ALL'
FILE_NAME += '_' + str(START_DATE.year) + '_' + str(END_DATE.year) \
              + '_' + TYPE + '_' + FORMAT + '_' + str(THRESHOLD) \
              + '_' + str(GRAPH_SMOOTH) + '.mp4'

fig, axs = pyplot.subplots(figsize=(12.8, 7.2))

all_dates = []
current_date = START_DATE
while current_date <= END_DATE:
  all_dates.append(current_date)
  current_date += ONE_DAY

print ('Writing:' + '\t' + FILE_NAME)
writer = animation.FFMpegWriter(fps=60, bitrate=5000)
with writer.saving(fig, FILE_NAME, dpi=100):
  current_date = START_DATE
  while current_date <= END_DATE:
    draw_for_date(current_date)
    writer.grab_frame()
    current_date += ONE_DAY
print ('Done:' + '\t' + FILE_NAME)

