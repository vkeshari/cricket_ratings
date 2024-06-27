from datetime import date, timedelta, datetime
from os import listdir

ONE_DAY = timedelta(days=1)
ONE_WEEK = timedelta(days=7)
ONE_MONTH = timedelta(days=30)
ONE_YEAR = timedelta(days=365)

# ['batting', 'bowling', 'allrounder']
TYPE = 'batting'
# ['test', 'odi', 't20']
FORMAT = 't20'

# Graph date range
START_DATE = date(2021, 1, 1)
END_DATE = date(2024, 1, 1)

# Min and MAX rating to show
THRESHOLD = 0
MAX_RATING = 1000
BIN_SIZE = 50

# Aggregation
# ['', 'monthly', 'quarterly', 'halfyearly', 'yearly']
AGGREGATION_WINDOW = ''
# ['', 'avg', 'median', 'min', 'max']
PLAYER_AGGREGATE = ''
# ['', 'avg', 'median', 'min', 'max']
BUCKET_AGGREGATE = ''

# Alternate way to calculate allrounder ratings. Use geometric mean of batting and bowling.
ALLROUNDERS_GEOM_MEAN = False

assert TYPE in ['batting', 'bowling', 'allrounder'], "Invalid TYPE provided"
assert FORMAT in ['test', 'odi', 't20'], "Invalid FORMAT provided"
assert START_DATE < END_DATE, "START_DATE must be earlier than END_DATE"
assert END_DATE <= date.today(), "Future END_DATE requested"

assert THRESHOLD >= 0, "THRESHOLD must not be negative"
assert MAX_RATING <= 1000, "MAX_RATING must not be greater than 1000"
assert BIN_SIZE > 0, "BIN_SIZE must be positive"
assert (MAX_RATING - THRESHOLD) % BIN_SIZE == 0, "BIN_SIZE must split ratings range evenly"

if AGGREGATION_WINDOW:
  assert AGGREGATION_WINDOW in ['monthly', 'quarterly', 'halfyearly', 'yearly'], \
        "Invalid AGGREGATION_WINDOW provided"
  assert PLAYER_AGGREGATE or BUCKET_AGGREGATE, \
        "AGGREGATION_WINDOW provided but no aggregation requested"
if PLAYER_AGGREGATE:
  assert AGGREGATION_WINDOW, "Aggregation requested but no AGGREGATION_WINDOW provided"
  assert not BUCKET_AGGREGATE, "Only one of PLAYER_AGGREGATE or BUCKET_AGGREGATE supported"
  assert PLAYER_AGGREGATE in ['avg', 'median', 'min', 'max'], \
        "Invalid PLAYER_AGGREGATE provided"
if BUCKET_AGGREGATE:
  assert AGGREGATION_WINDOW, "Aggregation requested but no AGGREGATION_WINDOW provided"
  assert not PLAYER_AGGREGATE, "Only one of PLAYER_AGGREGATE or BUCKET_AGGREGATE supported"
  assert BUCKET_AGGREGATE in ['avg', 'median', 'min', 'max'], \
        "Invalid BUCKET_AGGREGATE provided"

print (FORMAT + '\t' + TYPE)
print (str(START_DATE) + ' to ' + str(END_DATE))

def string_to_date(s):
  dt = datetime.strptime(s, '%Y%m%d')
  return date(dt.year, dt.month, dt.day)

def readable_name(p):
  sep = p.find('_')
  return p[sep+1:].split('.')[0].replace('_', ' ')

def country(p):
  return p.split('_')[0]

def full_readable_name(p):
  return readable_name(p) + ' (' + country(p) + ')'

def get_daily_ratings():
  daily_ratings = {}

  player_files = listdir('players/' + TYPE + '/' + FORMAT)
  for p in player_files:
    lines = []
    with open('players/' + TYPE + '/' + FORMAT + '/' + p, 'r') as f:
      lines += f.readlines()

    for l in lines:
      parts = l.split(',')
      d = string_to_date(parts[0])
      if d not in daily_ratings:
        daily_ratings[d] = {}

      rating = eval(parts[2])
      daily_ratings[d][p] = rating

  daily_ratings = dict(sorted(daily_ratings.items()))
  for d in daily_ratings:
    daily_ratings[d] = dict(sorted(daily_ratings[d].items(), \
                                    key = lambda item: item[1], reverse = True))

  return daily_ratings

daily_ratings = get_daily_ratings()
print("Daily ratings data built for " + str(len(daily_ratings)) + " days" )

bins = range(THRESHOLD, MAX_RATING + 1, BIN_SIZE)

def get_dates_to_plot():
  dates_to_plot = []
  d = START_DATE
  while d <= END_DATE:
    dates_to_plot.append(d)
    d += ONE_DAY
  return dates_to_plot
dates_to_plot = get_dates_to_plot()

def is_aggregation_window_start(d):
  return AGGREGATION_WINDOW == 'monthly' and d.day == 1 \
      or AGGREGATION_WINDOW == 'quarterly' and d.day == 1 and d.month in [1, 4, 7, 10] \
      or AGGREGATION_WINDOW == 'halfyearly' and d.day == 1 and d.month in [1, 7] \
      or AGGREGATION_WINDOW == 'yearly' and d.day == 1 and d.month == 1 \

def get_aggregate_ratings(daily_ratings):
  aggregate_ratings = daily_ratings
  # ...
  return aggregate_ratings

if AGGREGATION_WINDOW:
  dates_to_plot = [START_DATE]
  dates_to_plot += [d for d in range(START_DATE + 1, END_DATE + 1, ONE_DAY) \
                          if is_aggregation_window_start(d)]
  daily_ratings = get_aggregate_ratings(daily_ratings)
  print("Aggregate ratings built with " + str(len(daily_ratings)) \
            + "aggregate windows" )

from matplotlib import pyplot, animation

def draw_for_date(current_date):
  if current_date.day == 1:
    print (current_date)
  axs.clear()

  title_text = "Distribution of " + FORMAT + ' ' + TYPE + " ratings" \
                + '\n' + str(START_DATE) + " to " + str(END_DATE)
  axs.set_title(title_text, fontsize ='xx-large')

  axs.set_ylabel("No. of players", fontsize ='x-large')

  axs.set_ylim(0, BIN_SIZE)
  yticks = range(0, BIN_SIZE + 1, 5)
  axs.set_yticks(yticks)
  axs.set_yticklabels([str(y) for y in yticks], fontsize ='large')

  axs.set_xlabel("Rating", fontsize ='x-large')

  axs.set_xlim(THRESHOLD, MAX_RATING)
  xtick_spacing = BIN_SIZE
  if (MAX_RATING - THRESHOLD) / BIN_SIZE > 10:
    xtick_spacing = BIN_SIZE * 2
  xticks = range(THRESHOLD, MAX_RATING + 1, xtick_spacing)
  axs.set_xticks(xticks)
  axs.set_xticklabels([str(x) for x in xticks], fontsize ='large', rotation = 45)

  axs.grid(True, which = 'both', axis = 'both', alpha = 0.5)

  day_ratings = daily_ratings[current_date].values()

  axs.hist(day_ratings, bins = bins, \
            range = (THRESHOLD, MAX_RATING), \
            align = 'mid', \
            color = 'blue', alpha = 0.7)

  pyplot.text(x = MAX_RATING - 10, y = BIN_SIZE - 1, s = str(current_date), \
                alpha = 0.8, fontsize = 'x-large', \
                horizontalalignment = 'right', verticalalignment = 'top')

  pyplot.draw()

FILE_NAME = 'out/HIST_' + str(START_DATE.year) + '_' + str(END_DATE.year) \
              + '_' + TYPE + '_' + FORMAT + '_' + str(THRESHOLD) \
              + '_' + str(BIN_SIZE) + '.mp4'

resolution = (7.2, 7.2)

fig, axs = pyplot.subplots(figsize = resolution)

fps = 60
if AGGREGATION_WINDOW == 'monthly':
  fps = 2
elif AGGREGATION_WINDOW in ['quarterly', 'halfyearly', 'yearly']:
  fps = 1

print ('Writing:' + '\t' + FILE_NAME)
writer = animation.FFMpegWriter(fps = fps, bitrate = 5000)
with writer.saving(fig, FILE_NAME, dpi = 100):
  for current_date in dates_to_plot:
    draw_for_date(current_date)
    writer.grab_frame()
print ('Done:' + '\t' + FILE_NAME)