import math

from datetime import date, timedelta, datetime
from os import listdir
from pathlib import Path
import numpy as np

ONE_DAY = timedelta(days = 1)

# ['batting', 'bowling', 'allrounder']
TYPE = 'batting'
# ['test', 'odi', 't20']
FORMAT = 'odi'

# Graph date range
START_DATE = date(1981, 1, 1)
END_DATE = date(2024, 1, 1)

# Upper and lower bounds of ratings to show
THRESHOLD = 500
MAX_RATING = 1000
BIN_SIZE = 20

# Aggregation
# ['', 'monthly', 'quarterly', 'halfyearly', 'yearly', 'decadal']
AGGREGATION_WINDOW = 'yearly'
# ['', 'avg', 'median', 'min', 'max', 'first', 'last']
PLAYER_AGGREGATE = ''
# ['', 'avg', 'median', 'min', 'max', 'first', 'last']
BIN_AGGREGATE = 'avg'

# Alternate way to calculate allrounder ratings. Use geometric mean of batting and bowling.
ALLROUNDERS_GEOM_MEAN = True

assert TYPE in ['batting', 'bowling', 'allrounder'], "Invalid TYPE provided"
assert FORMAT in ['test', 'odi', 't20'], "Invalid FORMAT provided"
assert START_DATE < END_DATE, "START_DATE must be earlier than END_DATE"
assert END_DATE <= date.today(), "Future END_DATE requested"

assert THRESHOLD >= 0, "THRESHOLD must not be negative"
assert MAX_RATING <= 1000, "MAX_RATING must not be greater than 1000"
assert BIN_SIZE >= 10, "BIN_SIZE must be at least 10"
assert (MAX_RATING - THRESHOLD) % BIN_SIZE == 0, "BIN_SIZE must split ratings range evenly"

if AGGREGATION_WINDOW:
  assert PLAYER_AGGREGATE or BIN_AGGREGATE, \
        "AGGREGATION_WINDOW provided but no aggregation requested"
  assert AGGREGATION_WINDOW in ['monthly', 'quarterly', 'halfyearly', 'yearly', 'decadal'], \
        "Invalid AGGREGATION_WINDOW provided"
if PLAYER_AGGREGATE:
  assert AGGREGATION_WINDOW, "Aggregation requested but no AGGREGATION_WINDOW provided"
  assert not BIN_AGGREGATE, "Only one of PLAYER_AGGREGATE or BIN_AGGREGATE supported"
  assert PLAYER_AGGREGATE in ['avg', 'median', 'min', 'max', 'first', 'last'], \
        "Invalid PLAYER_AGGREGATE provided"
if BIN_AGGREGATE:
  assert AGGREGATION_WINDOW, "Aggregation requested but no AGGREGATION_WINDOW provided"
  assert not PLAYER_AGGREGATE, "Only one of PLAYER_AGGREGATE or BIN_AGGREGATE supported"
  assert BIN_AGGREGATE in ['avg', 'median', 'min', 'max', 'first', 'last'], \
        "Invalid BIN_AGGREGATE provided"

print (FORMAT + '\t' + TYPE)
print (str(START_DATE) + ' to ' + str(END_DATE))
print (str(THRESHOLD) + ' : ' + str(BIN_SIZE) + ' : ' + str(MAX_RATING))
if AGGREGATION_WINDOW:
  print (AGGREGATION_WINDOW + ' / ' + PLAYER_AGGREGATE + ' / ' + BIN_AGGREGATE)

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
      if TYPE == 'allrounder' and ALLROUNDERS_GEOM_MEAN:
        rating = int(math.sqrt(rating * 1000))
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
      or AGGREGATION_WINDOW == 'decadal' and d.day == 1 and d.month == 1 \
                                        and d.year % 10 == 1

def aggregate_values(values, agg_type):
  if agg_type == 'avg':
    return np.average(values)
  if agg_type == 'median':
    return np.percentile(values, 50)
  if agg_type == 'min':
    return min(values)
  if agg_type == 'max':
    return max(values)
  if agg_type == 'first':
    return values[0]
  if agg_type == 'last':
    return values[-1]

def get_aggregate_ratings(daily_ratings):
  if not AGGREGATION_WINDOW:
    return daily_ratings

  aggregate_ratings = {}
  first_date = min(daily_ratings.keys())
  last_date = max(daily_ratings.keys())

  if PLAYER_AGGREGATE:
    bucket_values = {}
    last_window_start = first_date
    for d in daily_ratings:
      if d not in aggregate_ratings:
        aggregate_ratings[d] = {}
      if d == last_date or is_aggregation_window_start(d):
        for p in bucket_values:
          aggregate_ratings[last_window_start][p] = \
                  aggregate_values(bucket_values[p], PLAYER_AGGREGATE)
        bucket_values = {}
        last_window_start = d
      else:
        aggregate_ratings[d] = aggregate_ratings[last_window_start]

      for p in daily_ratings[d]:
        if p not in bucket_values:
          bucket_values[p] = []
        bucket_values[p].append(daily_ratings[d][p])

  elif BIN_AGGREGATE:
    bucket_values = {}
    last_window_start = first_date
    for d in daily_ratings:
      if d not in aggregate_ratings:
        aggregate_ratings[d] = {}
      if d == last_date or is_aggregation_window_start(d):
        for b in bucket_values:
          aggregate_ratings[last_window_start][b] = \
                  aggregate_values(bucket_values[b], BIN_AGGREGATE)
        bucket_values = {}
        last_window_start = d
      else:
        aggregate_ratings[d] = aggregate_ratings[last_window_start]

      day_bin_counts = {}
      day_player_total = 0 # used to normalize
      for p in daily_ratings[d]:
        player_rating = daily_ratings[d][p]
        player_bin_number = int((player_rating - THRESHOLD) / BIN_SIZE)
        if player_bin_number < 0:
          continue
        player_bin = THRESHOLD + player_bin_number * BIN_SIZE

        if player_bin not in day_bin_counts:
          day_bin_counts[player_bin] = 0
        day_bin_counts[player_bin] += 1
        day_player_total += 1

      for b in day_bin_counts:
        if b not in bucket_values:
          bucket_values[b] = []
        bucket_values[b].append(day_bin_counts[b] * BIN_SIZE / (2 * day_player_total))

  return aggregate_ratings

if AGGREGATION_WINDOW:
  dates_to_plot = [START_DATE]
  d = START_DATE + ONE_DAY
  while d < END_DATE:
    if is_aggregation_window_start(d):
      dates_to_plot.append(d)
    d += ONE_DAY
  if END_DATE not in dates_to_plot:
    dates_to_plot.append(END_DATE)

  daily_ratings = get_aggregate_ratings(daily_ratings)
  print(AGGREGATION_WINDOW + " aggregate ratings built")

from matplotlib import pyplot, animation

def draw_for_date(current_date):
  if current_date.day == 1:
    print (current_date)
  axs.clear()

  title_text = "Distribution of " + FORMAT + ' ' + TYPE + " ratings" \
                + '\n' + str(START_DATE) + " to " + str(END_DATE)
  axs.set_title(title_text, fontsize ='xx-large')

  axs.set_ylabel("No. of players", fontsize ='x-large')

  max_y = int(BIN_SIZE / 2)
  axs.set_ylim(0, max_y)
  yticks = range(0, max_y + 1, 5)
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

  text_spacing = BIN_SIZE / 50

  pyplot.text(x = MAX_RATING - 10, y = max_y - text_spacing, s = str(current_date), \
                alpha = 0.8, fontsize = 'x-large', \
                horizontalalignment = 'right', verticalalignment = 'top')

  color = 'darkgrey'
  if TYPE == 'batting':
    color = 'red'
  if TYPE == 'bowling':
    color = 'blue'
  if TYPE == 'allrounder':
    color = 'green'

  if PLAYER_AGGREGATE:
    day_ratings_to_show = []
    if current_date in daily_ratings:
      day_ratings = daily_ratings[current_date].values()
      day_ratings_to_show = [r for r in day_ratings if r >= THRESHOLD and r <= MAX_RATING]

      axs.hist(day_ratings_to_show, bins = bins, \
                align = 'mid', \
                color = color, alpha = 0.7)

    pyplot.text(x = MAX_RATING - 10, y = max_y - 2 * text_spacing, \
                  s = 'Players shown: ' + str(len(day_ratings_to_show)), \
                  alpha = 0.8, fontsize = 'x-large', \
                  horizontalalignment = 'right', verticalalignment = 'top')

    pyplot.text(x = MAX_RATING - 10, y = max_y - 3 * text_spacing, \
                  s = 'Aggregation: ' + AGGREGATION_WINDOW + ' ' + PLAYER_AGGREGATE, \
                  alpha = 0.8, fontsize = 'x-large', \
                  horizontalalignment = 'right', verticalalignment = 'top')

  elif BIN_AGGREGATE:
    if current_date in daily_ratings:
      (xs, ys) = zip(*sorted(daily_ratings[current_date].items()))

      axs.bar(xs, ys, align = 'edge', width = BIN_SIZE, color = color, alpha = 0.7)

    pyplot.text(x = MAX_RATING - 10, y = max_y - 2 * text_spacing, \
                  s = 'Normalized player count: ' + str(round(sum(ys))), \
                  alpha = 0.8, fontsize = 'x-large', \
                  horizontalalignment = 'right', verticalalignment = 'top')

    pyplot.text(x = MAX_RATING - 10, y = max_y - 3 * text_spacing, \
                  s = 'Aggregation: ' + AGGREGATION_WINDOW + ' ' + BIN_AGGREGATE, \
                  alpha = 0.8, fontsize = 'x-large', \
                  horizontalalignment = 'right', verticalalignment = 'top')

  pyplot.draw()

resolution = (7.2, 7.2)
fig, axs = pyplot.subplots(figsize = resolution)

aggregation_filename = ''
if AGGREGATION_WINDOW:
  if PLAYER_AGGREGATE:
    aggregation_filename += '_' + AGGREGATION_WINDOW + '_' + PLAYER_AGGREGATE + '_BYPLAYER'
  elif BIN_AGGREGATE:
    aggregation_filename += '_' + AGGREGATION_WINDOW + '_' + BIN_AGGREGATE + '_BYBIN'
type_filename = TYPE
if TYPE == 'allrounder':
  if ALLROUNDERS_GEOM_MEAN:
    type_filename += 'Geom'
  else:
    type_filename += '1000'
FILE_NAME = 'out/hist/HIST_' + str(START_DATE.year) + '_' + str(END_DATE.year) \
              + '_' + type_filename + '_' + FORMAT + '_' + str(THRESHOLD) \
              + '_' + str(BIN_SIZE) + aggregation_filename + '.mp4'
Path(FILE_NAME).parent.mkdir(exist_ok = True, parents = True)

fps = 60
if AGGREGATION_WINDOW == 'monthly':
  fps = 6
elif AGGREGATION_WINDOW in ['quarterly', 'halfyearly', 'yearly', 'decadal']:
  fps = 2

print ('Writing:' + '\t' + FILE_NAME)
writer = animation.FFMpegWriter(fps = fps, bitrate = 5000)
with writer.saving(fig, FILE_NAME, dpi = 100):
  for current_date in dates_to_plot:
    draw_for_date(current_date)
    writer.grab_frame()
print ('Done:' + '\t' + FILE_NAME)