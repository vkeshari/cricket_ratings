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

# Min rating to show
THRESHOLD = 500

# Alternate way to calculate allrounder ratings. Use geometric mean of batting and bowling.
ALLROUNDERS_GEOM_MEAN = False

assert TYPE in ['batting', 'bowling', 'allrounder'], "Invalid TYPE provided"
assert FORMAT in ['test', 'odi', 't20'], "Invalid FORMAT provided"
assert START_DATE < END_DATE, "START_DATE must be earlier than END_DATE"
assert END_DATE <= date.today(), "Future END_DATE requested"
assert THRESHOLD >= 0, "THRESHOLD must not be negative"

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

from matplotlib import pyplot, axes, cm, animation

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

def country_color(country):
  if country in country_colors:
    return country_colors[country]
  else:
    return 'darkgrey'

def draw_for_date(current_date):
  axs.clear()
  pyplot.draw()

FILE_NAME = 'out/HIST_'
if len(COUNTRY_PREFIX) > 0:
  FILE_NAME += COUNTRY_PREFIX
else:
  FILE_NAME += 'ALL'
FILE_NAME += '_' + str(START_DATE.year) + '_' + str(END_DATE.year) \
              + '_' + TYPE + '_' + FORMAT + '_' + str(THRESHOLD) + '.mp4'

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