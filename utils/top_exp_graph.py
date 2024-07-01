import math

from datetime import date, timedelta, datetime
from os import listdir
from pathlib import Path
import numpy as np

ONE_DAY = timedelta(days = 1)

# ['batting', 'bowling', 'allrounder']
TYPE = 'batting'
# ['test', 'odi', 't20']
FORMAT = 't20'

# Graph date range
START_DATE = date(2021, 1, 1)
END_DATE = date(2024, 1, 1)
SKIP_YEARS = list(range(1913, 1921)) + list(range(1940, 1946)) + [2020]

# Upper and lower bounds of ratings to show
THRESHOLD = 500
MAX_RATING = 1000

# Aggregation
# ['', 'monthly', 'quarterly', 'halfyearly', 'yearly', 'decadal']
AGGREGATION_WINDOW = 'yearly'
# ['', 'avg', 'median', 'min', 'max', 'first', 'last']
PLAYER_AGGREGATE = 'max'
# ['', 'avg', 'median', 'min', 'max', 'first', 'last']
BIN_AGGREGATE = 'avg'

EXP_BIN_SIZE = 10

MAX_SIGMA = 3.0
MIN_SIGMA = 1.0
# [0.05, 0.1, 0.2, 0.5]
SIGMA_STEP = 0.05

SIGMA_BINS = round((MAX_SIGMA - MIN_SIGMA) / SIGMA_STEP)

CUMULATIVES = True
BY_MEDAL_PERCENTAGES = False

AVG_MEDAL_CUMULATIVE_COUNTS = {'gold': 2, 'silver': 5, 'bronze': 10}

SHOW_BIN_COUNTS = False
SHOW_GRAPH = True

EPOCH = date(1900, 1, 1)

# Alternate way to calculate allrounder ratings. Use geometric mean of batting and bowling.
ALLROUNDERS_GEOM_MEAN = True

assert TYPE in ['batting', 'bowling', 'allrounder'], "Invalid TYPE provided"
assert FORMAT in ['test', 'odi', 't20'], "Invalid FORMAT provided"
assert START_DATE < END_DATE, "START_DATE must be earlier than END_DATE"
assert END_DATE <= date.today(), "Future END_DATE requested"

assert THRESHOLD >= 0, "THRESHOLD must not be negative"
assert MAX_RATING <= 1000, "MAX_RATING must not be greater than 1000"

assert AGGREGATION_WINDOW in ['monthly', 'quarterly', 'halfyearly', 'yearly', 'decadal'], \
      "Invalid AGGREGATION_WINDOW provided"
assert PLAYER_AGGREGATE in ['avg', 'median', 'min', 'max', 'first', 'last'], \
      "Invalid PLAYER_AGGREGATE provided"
assert BIN_AGGREGATE in ['avg', 'median', 'min', 'max', 'first', 'last'], \
      "Invalid BIN_AGGREGATE provided"

assert EXP_BIN_SIZE >= 10, "EXP_BIN_SIZE must be at least 10"
assert MAX_SIGMA >= 1.0, "MAX_SIGMA must greater than 1.0"
assert MIN_SIGMA >= 0.0 and MIN_SIGMA < MAX_SIGMA, \
      "MIN_SIGMA must be between 0.0 and MAX_SIGMA"
assert SIGMA_STEP in [0.05, 0.1, 0.2, 0.5], "Invalid SIGMA_STEP provided"

assert not set(AVG_MEDAL_CUMULATIVE_COUNTS.keys()) - {'gold', 'silver', 'bronze'}, \
    'AVG_MEDAL_CUMULATIVE_COUNTS keys must be gold silver and bronze'
for amcc in AVG_MEDAL_CUMULATIVE_COUNTS.values():
  assert amcc > 0, "All values in AVG_MEDAL_CUMULATIVE_COUNTS must be positive"

print (FORMAT + '\t' + TYPE)
print (str(START_DATE) + ' to ' + str(END_DATE))
print (str(THRESHOLD) + ' : ' + str(MAX_RATING))
print (AGGREGATION_WINDOW + ' / ' + BIN_AGGREGATE + ' / ' + PLAYER_AGGREGATE)

def string_to_date(s):
  dt = datetime.strptime(s, '%Y%m%d')
  return date(dt.year, dt.month, dt.day)

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

first_date = min(daily_ratings.keys())
last_date = max(daily_ratings.keys())

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
    return np.percentile(values, 50, method = 'nearest')
  if agg_type == 'min':
    return min(values)
  if agg_type == 'max':
    return max(values)
  if agg_type == 'first':
    return values[0]
  if agg_type == 'last':
    return values[-1]

def get_aggregate_ratings(daily_ratings):
  if not AGGREGATION_WINDOW or not PLAYER_AGGREGATE:
    return daily_ratings

  aggregate_ratings = {}

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

  return aggregate_ratings

aggregate_ratings = get_aggregate_ratings(daily_ratings)
print(AGGREGATION_WINDOW + " aggregate ratings built")

dates_to_show = []
d = first_date
while d <= last_date:
  if d >= START_DATE and d <= END_DATE and is_aggregation_window_start(d):
    dates_to_show.append(d)
  d += ONE_DAY

def get_exp_medians(daily_ratings):
  if not AGGREGATION_WINDOW:
    return daily_ratings

  exp_medians = {}
  exp_buckets = {}
  exp_bin_stops = list(range(THRESHOLD, MAX_RATING, EXP_BIN_SIZE)) + [MAX_RATING]

  current_bucket = {}
  d = first_date
  last_d = EPOCH
  while d <= last_date:
    if d in dates_to_show and current_bucket:
      bucket_days = len(current_bucket)
      cum_counts = [0] * (len(exp_bin_stops) - 1)
      for cbd in current_bucket:
        counts = current_bucket[cbd]
        sum_counts = sum(counts)
        for i, v in enumerate(counts):
          cum_counts[i] += int(v) * 100 / (sum_counts * bucket_days)
      exp_buckets[last_d] = cum_counts
      current_bucket = {}
      last_d = d
    else:
      current_bucket[d] = np.histogram(list(daily_ratings[d].values()), \
                                        bins = exp_bin_stops
                                      )[0]

    d += ONE_DAY

  for d in exp_buckets:
    bin_vals = exp_buckets[d]
    median_rating = sum(bin_vals) / 2

    cum_val = 0
    for i, v in enumerate(bin_vals):
      cum_val += v
      if cum_val >= median_rating:
        exp_medians[d] = exp_bin_stops[i]
        break

  return exp_medians

exp_medians = get_exp_medians(daily_ratings)
print(AGGREGATION_WINDOW + " exp medians built")

metrics_bins = {}
sigma_stops = np.linspace(MIN_SIGMA, MAX_SIGMA, SIGMA_BINS + 1)
actual_sigma_stops = sigma_stops[ : -1]
for r in actual_sigma_stops:
  metrics_bins[r] = []

if SHOW_BIN_COUNTS:
  print('\n=== Player count in each rating sigma bin ===')
  h = 'AGG START DATE'
  for b in actual_sigma_stops:
    h += '\t' + '{b:.2f}'.format(b = b)
  print(h)

player_medals = {}
player_periods = {}

for i, d in enumerate(dates_to_show):
  if d.year in SKIP_YEARS:
    del dates_to_show[i]
if dates_to_show[-1] == END_DATE:
  dates_to_show.pop()

for d in dates_to_show:
  ratings_in_range = {k: v for k, v in aggregate_ratings[d].items() \
                      if v >= THRESHOLD and v <= MAX_RATING}
  
  median_val = exp_medians[d]

  bin_counts = [0] * len(sigma_stops)
  bin_players = []
  for r in sigma_stops:
    bin_players.append([])
  for p in ratings_in_range:
    rating = ratings_in_range[p]
    if p not in player_periods:
      player_periods[p] = 0
    player_periods[p] += 1

    #print (str(THRESHOLD) + '\t' + str(rating) + '\t' + str(median_val))
    rating_sigma = (rating - THRESHOLD) / (median_val - THRESHOLD)
    if rating_sigma < sigma_stops[0]:
      continue
    for i, r in enumerate(sigma_stops):
      if rating_sigma < r:
        bin_counts[i - 1] += 1
        bin_players[i - 1].append(p)
        break
      if rating_sigma == r:
        bin_counts[i] += 1
        bin_players[i].append(p)
        break
  bin_counts[-2] += bin_counts[-1]
  bin_players[-2] += bin_players[-1]

  for i, r in enumerate(actual_sigma_stops):
    metrics_bins[r].append(bin_counts[i])

  for i, r in enumerate(actual_sigma_stops):
    for p in bin_players[i]:
      if p not in player_medals:
        player_medals[p] = {}
        for rs in actual_sigma_stops:
          player_medals[p][rs] = 0
      player_medals[p][r] += 1

if BY_MEDAL_PERCENTAGES:
  for p in player_medals:
    for r in player_medals[p]:
      player_medals[p][r] = 100 * player_medals[p][r] / player_periods[p]

  if SHOW_BIN_COUNTS:
    s = str(d)
    for b in bin_counts[ : -1]:
      s += '\t' + str(b)
    print (s)

for r in actual_sigma_stops:
  player_medals = dict(sorted(player_medals.items(),
                                key = lambda item: item[1][r], reverse = True))


graph_metrics = {'starts': [], 'ends': [], 'widths': [], \
                  'starts_in': [], 'ends_in': [], 'widths_in': [], \
                   'lines': [], 'avgs': []}

cum_metrics_bins = {}
for r in actual_sigma_stops:
  cum_metrics_bins[r] = [0] * len(dates_to_show)

last_r = -1
for r in reversed(actual_sigma_stops):
  for i, v in enumerate(metrics_bins[r]):
    if last_r == -1:
      cum_metrics_bins[r][i] = 0
    else:
      cum_metrics_bins[r][i] = cum_metrics_bins[last_r][i]
    cum_metrics_bins[r][i] += v
  last_r = r

  if CUMULATIVES:
    start = np.percentile(cum_metrics_bins[r], 10, method = 'nearest')
    end = np.percentile(cum_metrics_bins[r], 90, method = 'nearest')
    width = end - start
    start_in = np.percentile(cum_metrics_bins[r], 20, method = 'nearest')
    end_in = np.percentile(cum_metrics_bins[r], 80, method = 'nearest')
    width_in = end_in - start_in
    line = (min(cum_metrics_bins[r]), max(cum_metrics_bins[r]))
    avg = np.average(cum_metrics_bins[r])
  else:
    start = np.percentile(metrics_bins[r], 10, method = 'nearest')
    end = np.percentile(metrics_bins[r], 90, method = 'nearest')
    width = end - start
    start_in = np.percentile(metrics_bins[r], 20, method = 'nearest')
    end_in = np.percentile(metrics_bins[r], 80, method = 'nearest')
    width_in = end_in - start_in
    line = (min(metrics_bins[r]), max(metrics_bins[r]))
    avg = np.average(metrics_bins[r])

  graph_metrics['starts'].append(start)
  graph_metrics['ends'].append(end)
  graph_metrics['widths'].append(width)
  graph_metrics['starts_in'].append(start_in)
  graph_metrics['ends_in'].append(end_in)
  graph_metrics['widths_in'].append(width_in)
  graph_metrics['lines'].append(line)
  graph_metrics['avgs'].append(avg)

medal_indices = {'gold': -1, 'silver': -1, 'bronze': -1}
for i, av in enumerate(graph_metrics['avgs']):
  for medal in medal_indices:
    if medal_indices[medal] == -1:
      medal_desired =  AVG_MEDAL_CUMULATIVE_COUNTS[medal]
      if av > medal_desired:
        if av - medal_desired > medal_desired - graph_metrics['avgs'][i -1]:
          medal_indices[medal] = i - 1
        else:
          medal_indices[medal] = i

gold_sigma = list(reversed(actual_sigma_stops))[medal_indices['gold']]
silver_sigma = list(reversed(actual_sigma_stops))[medal_indices['silver']]
bronze_sigma = list(reversed(actual_sigma_stops))[medal_indices['bronze']]

gold_exp_num = graph_metrics['avgs'][medal_indices['gold']]
silver_exp_num = graph_metrics['avgs'][medal_indices['silver']]
bronze_exp_num = graph_metrics['avgs'][medal_indices['bronze']]

print ('\nGold:\t{g:.2f}\tSilver:\t{s:.2f}\tBronze:\t{b:.2f}'.format(
                    g = gold_sigma, s = silver_sigma, b = bronze_sigma))

if SHOW_GRAPH:
  from matplotlib import pyplot as plt

  resolution = tuple([7.2, 7.2])
  fig, ax = plt.subplots(figsize = resolution)

  TITLE_TEXT = "No. of players above sigma values\n " \
                + FORMAT + ' ' + TYPE + ' (' + str(START_DATE) \
                          + ' to ' + str(END_DATE) + ')'
  ax.set_title(TITLE_TEXT, fontsize ='xx-large')

  ax.set_ylabel('Rating sigma', fontsize ='x-large')
  ax.set_xlabel('No. of players above sigma threshold', fontsize ='x-large')

  ymin = MIN_SIGMA - SIGMA_STEP
  ymax = MAX_SIGMA
  ax.set_ylim(ymin, ymax)
  ax.set_yticks(actual_sigma_stops)
  ax.set_yticklabels(['{v:.2f}'.format(v = r) for r in actual_sigma_stops], \
                          fontsize ='medium')

  xmax = int(graph_metrics['ends'][-1]) + 2
  ax.set_xlim(0, xmax)
  xticks = list(range(0, xmax + 1, 1))
  ax.set_xticks(xticks)

  xlabwidth = 1
  if graph_metrics['ends'][-1] > 25:
    xlabwidth = 2
  if graph_metrics['ends'][-1] > 50:
    xlabwidth = 5
  if graph_metrics['ends'][-1] > 100:
    xlabwidth = 10
  xticklabels = [str(x) if x % xlabwidth == 0 else '' for x in xticks]
  ax.set_xticklabels(xticklabels, fontsize ='medium')

  ax.grid(True, which = 'both', axis = 'x', alpha = 0.5)

  ax.barh(y = list(reversed(actual_sigma_stops)), width = graph_metrics['widths'], \
            align = 'center', height = 0.9 * SIGMA_STEP, left = graph_metrics['starts'], \
            color = 'darkgrey', alpha = 0.4, \
          )
  ax.barh(y = list(reversed(actual_sigma_stops)), width = graph_metrics['widths_in'], \
          align = 'center', height = 0.8 * SIGMA_STEP, left = graph_metrics['starts_in'], \
          color = 'green', alpha = 0.5, \
        )
  plt.plot(graph_metrics['avgs'], list(reversed(actual_sigma_stops)), \
                    linewidth = 0, alpha = 0.5, \
                    marker = 'x', markeredgecolor = 'blue', \
                    markersize = 8, markeredgewidth = 2)
  for i, r in enumerate(reversed(actual_sigma_stops)):
    plt.plot(list(graph_metrics['lines'][i]), [r, r], linewidth = 2, \
                      color = 'black', alpha = 0.9, \
                      marker = 'o', markerfacecolor = 'red', \
                      markersize = 3, markeredgewidth = 0)

  gold_label = '{v:.2f}'.format(v = gold_exp_num)
  plt.axhline(y = gold_sigma, linestyle = '--', linewidth = 1, \
                color = 'black', alpha = 0.8)
  plt.text(x = xmax - 1, y = gold_sigma, s = 'Gold', alpha = 0.8, fontsize = 'large', \
                horizontalalignment = 'right', verticalalignment = 'bottom')
  gold_ymax_sigma = (gold_sigma - ymin) / (ymax - ymin)
  plt.axvline(x = gold_exp_num, linestyle = ':', linewidth = 1, \
                color = 'black', alpha = 0.8, ymax = gold_ymax_sigma)

  silver_label = '{v:.2f}'.format(v = silver_exp_num)
  plt.axhline(y = silver_sigma, linestyle = '--', linewidth = 1, \
                color = 'black', alpha = 0.8)
  plt.text(x = xmax - 1, y = silver_sigma, s = 'Silver', alpha = 0.8, fontsize = 'large', \
                horizontalalignment = 'right', verticalalignment = 'bottom')
  silver_ymax_sigma = (silver_sigma - ymin) / (ymax - ymin)
  plt.axvline(x = silver_exp_num, linestyle = ':', linewidth = 1, \
                color = 'black', alpha = 0.8, ymax = silver_ymax_sigma)

  bronze_label = '{v:.2f}'.format(v = bronze_exp_num)
  plt.axhline(y = bronze_sigma, linestyle = '--', linewidth = 1, \
                color = 'black', alpha = 0.8)
  plt.text(x = xmax - 1, y = bronze_sigma, s = 'Bronze', alpha = 0.8, fontsize = 'large', \
                horizontalalignment = 'right', verticalalignment = 'bottom')
  bronze_ymax_sigma = (bronze_sigma - ymin) / (ymax - ymin)
  plt.axvline(x = bronze_exp_num, linestyle = ':', linewidth = 1, \
                color = 'black', alpha = 0.8, ymax = bronze_ymax_sigma)

  fig.tight_layout()
  plt.show()
