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

# Empty or country code
COUNTRY_PREFIX = ''

# Graph date range
START_DATE = date(2021, 1, 1)
END_DATE = date(2024, 1, 1)

# Min and MAX rating to show
THRESHOLD = 0
MAX_RATING = 1000
BIN_SIZE = 50

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

def get_daily_ratings(typ, frmt, start_date, end_date, threshold, country_prefix):
  daily_ratings = {}

  player_files = listdir('players/' + typ + '/' + frmt)
  for p in player_files:
    if len(COUNTRY_PREFIX) > 0:
      continue

    lines = []
    with open('players/' + typ + '/' + frmt + '/' + p, 'r') as f:
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

daily_ratings = get_daily_ratings(TYPE, FORMAT, START_DATE, END_DATE, \
                                      THRESHOLD, COUNTRY_PREFIX)
print("Daily ratings data built for " + str(len(daily_ratings)) + " days." )

from matplotlib import pyplot, animation

def draw_for_date(current_date):
  if current_date.day == 1:
    print (current_date)
  axs.clear()

  day_ratings = daily_ratings[current_date].values()

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

  bins = range(THRESHOLD, MAX_RATING + 1, BIN_SIZE)
  axs.hist(day_ratings, bins = bins, \
            range = (THRESHOLD, MAX_RATING), \
            align = 'mid', \
            color = 'blue', alpha = 0.7)

  pyplot.text(x = MAX_RATING - 10, y = BIN_SIZE - 1, s = str(current_date), \
                alpha = 0.8, fontsize = 'x-large', \
                horizontalalignment = 'right', verticalalignment = 'top')

  pyplot.draw()

FILE_NAME = 'out/HIST_'
if len(COUNTRY_PREFIX) > 0:
  FILE_NAME += COUNTRY_PREFIX
else:
  FILE_NAME += 'ALL'
FILE_NAME += '_' + str(START_DATE.year) + '_' + str(END_DATE.year) \
              + '_' + TYPE + '_' + FORMAT + '_' + str(THRESHOLD) \
              + '_' + str(BIN_SIZE) + '.mp4'

resolution = (7.2, 7.2)

fig, axs = pyplot.subplots(figsize = resolution)

print ('Writing:' + '\t' + FILE_NAME)
writer = animation.FFMpegWriter(fps=60, bitrate=5000)
with writer.saving(fig, FILE_NAME, dpi=100):
  current_date = START_DATE
  while current_date <= END_DATE:
    draw_for_date(current_date)
    writer.grab_frame()
    current_date += ONE_DAY
print ('Done:' + '\t' + FILE_NAME)