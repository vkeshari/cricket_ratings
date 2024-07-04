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
START_DATE = date(2009, 1, 1)
END_DATE = date(2024, 1, 1)
SKIP_YEARS = list(range(1913, 1921)) + list(range(1940, 1946)) + [2020]

# Upper and lower bounds of ratings to show
THRESHOLD = 0
MAX_RATING = 1000

# ['', 'rating', 'rank', 'either', 'both']
CHANGED_DAYS_CRITERIA = 'rating'

# Aggregation
# ['', 'monthly', 'quarterly', 'halfyearly', 'yearly', 'decadal']
AGGREGATION_WINDOW = 'yearly'
# ['', 'avg', 'median', 'min', 'max', 'first', 'last']
PLAYER_AGGREGATE = 'max'

THRESHOLD_RELATIVE = False

MAX_RATIO = 1.0
MIN_RATIO = 0.7
# [0.01, 0.02, 0.05, 0.1]
RATIO_STEP = 0.01

RATIO_BINS = round((MAX_RATIO - MIN_RATIO) / RATIO_STEP)

GRAPH_CUMULATIVES = True
BY_MEDAL_PERCENTAGES = False

AVG_MEDAL_CUMULATIVE_COUNTS = {'gold': 2, 'silver': 5, 'bronze': 10}

SHOW_BIN_COUNTS = False
SHOW_GRAPH = True

SHOW_TOP_PLAYERS = True
TOP_PLAYERS = 25

# Alternate way to calculate allrounder ratings. Use geometric mean of batting and bowling.
ALLROUNDERS_GEOM_MEAN = True

assert TYPE in ['batting', 'bowling', 'allrounder'], "Invalid TYPE provided"
assert FORMAT in ['test', 'odi', 't20'], "Invalid FORMAT provided"
assert START_DATE < END_DATE, "START_DATE must be earlier than END_DATE"
assert END_DATE <= date.today(), "Future END_DATE requested"

assert MAX_RATING <= 1000, "MAX_RATING must not be greater than 1000"
assert THRESHOLD >= 0 and THRESHOLD < MAX_RATING, \
      "THRESHOLD must be between 0 and MAX_RATING"

assert CHANGED_DAYS_CRITERIA in ['', 'rating', 'rank', 'either', 'both']

assert AGGREGATION_WINDOW in ['monthly', 'quarterly', 'halfyearly', 'yearly', 'decadal'], \
      "Invalid AGGREGATION_WINDOW provided"
assert PLAYER_AGGREGATE in ['avg', 'median', 'min', 'max', 'first', 'last'], \
      "Invalid PLAYER_AGGREGATE provided"

assert MAX_RATIO == 1.0, "MAX_RATIO must be 1.0"
assert MIN_RATIO > 0.0 and MIN_RATIO < 1.0, "MIN_RATIO must be between 0.0 and 1.0"
assert RATIO_STEP in [0.01, 0.02, 0.05, 0.1], "Invalid RATIO_STEP provided"

assert not set(AVG_MEDAL_CUMULATIVE_COUNTS.keys()) - {'gold', 'silver', 'bronze'}, \
    'AVG_MEDAL_CUMULATIVE_COUNTS keys must be gold silver and bronze'
for amcc in AVG_MEDAL_CUMULATIVE_COUNTS.values():
  assert amcc > 0, "All values in AVG_MEDAL_CUMULATIVE_COUNTS must be positive"

assert TOP_PLAYERS > 5, "TOP_PLAYERS must be at least 5"

print (FORMAT + '\t' + TYPE)
print (str(START_DATE) + ' to ' + str(END_DATE))
print (str(THRESHOLD) + ' : ' + str(MAX_RATING))
print (AGGREGATION_WINDOW + ' / ' + PLAYER_AGGREGATE)

def string_to_date(s):
  dt = datetime.strptime(s, '%Y%m%d')
  return date(dt.year, dt.month, dt.day)

def is_aggregation_window_start(d, agg_window):
  if not agg_window:
    return True
  return agg_window == 'monthly' and d.day == 1 \
      or agg_window == 'quarterly' and d.day == 1 and d.month in [1, 4, 7, 10] \
      or agg_window == 'halfyearly' and d.day == 1 and d.month in [1, 7] \
      or agg_window == 'yearly' and d.day == 1 and d.month == 1 \
      or agg_window == 'decadal' and d.day == 1 and d.month == 1 \
                                        and d.year % 10 == 1

def get_days_with_change(daily_data):
  changed_days = set()
  last_daily_data = {}
  for d in daily_data:
    changed = False
    if not last_daily_data:
      changed = True
    elif not sorted(daily_data[d].keys()) == sorted(last_daily_data.keys()):
      changed = True
    else:
      for p in daily_data[d]:
        if not daily_data[d][p] == last_daily_data[p]:
          changed = True
          break
    if changed:
      changed_days.add(d)
    last_daily_data = daily_data[d]

  return changed_days

def get_daily_ratings():
  daily_ratings = {}
  daily_ranks = {}
  dates_parsed = set()

  player_files = listdir('players/' + TYPE + '/' + FORMAT)
  for p in player_files:
    lines = []
    with open('players/' + TYPE + '/' + FORMAT + '/' + p, 'r') as f:
      lines += f.readlines()

    for l in lines:
      parts = l.split(',')
      d = string_to_date(parts[0])
      if d not in dates_parsed:
        dates_parsed.add(d)
        daily_ratings[d] = {}
        daily_ranks[d] = {}

      rating = eval(parts[2])
      if TYPE == 'allrounder' and ALLROUNDERS_GEOM_MEAN:
        rating = int(math.sqrt(rating * 1000))
      daily_ratings[d][p] = rating

      rank = eval(parts[1])
      daily_ranks[d][p] = rank

  daily_ratings = dict(sorted(daily_ratings.items()))
  daily_ranks = dict(sorted(daily_ranks.items()))
  for d in dates_parsed:
    daily_ratings[d] = dict(sorted(daily_ratings[d].items(), \
                                    key = lambda item: item[1], reverse = True))
    daily_ranks[d] = dict(sorted(daily_ranks[d].items(), \
                                    key = lambda item: item[1]))

  if CHANGED_DAYS_CRITERIA:
    rating_change_days = set()
    rank_change_days = set()
    if CHANGED_DAYS_CRITERIA in {'rating', 'either', 'both'}:
      rating_change_days = get_days_with_change(daily_ratings)
    if CHANGED_DAYS_CRITERIA in {'rank', 'either', 'both'}:
      rank_change_days = get_days_with_change(daily_ranks)

    change_days = set()
    if CHANGED_DAYS_CRITERIA in {'rating', 'rank', 'either'}:
      change_days = rating_change_days | rank_change_days
    elif CHANGED_DAYS_CRITERIA == 'both':
      change_days = rating_change_days & rank_change_days

    daily_ratings = dict(filter(lambda item: item[0] in change_days, \
                              daily_ratings.items()))
    daily_ranks = dict(filter(lambda item: item[0] in change_days, \
                            daily_ranks.items()))

  return daily_ratings, daily_ranks

daily_ratings, _ = get_daily_ratings()
print("Daily ratings data built for " + str(len(daily_ratings)) + " days" )

first_date = min(daily_ratings.keys())
last_date = max(daily_ratings.keys())

dates_to_show = []
d = first_date
while d <= last_date:
  if d >= START_DATE and d <= END_DATE \
          and is_aggregation_window_start(d, AGGREGATION_WINDOW):
    dates_to_show.append(d)
  d += ONE_DAY

bin_by_date = np.searchsorted(dates_to_show, list(daily_ratings.keys()), side = 'right')
date_to_bucket = {}
for i, d in enumerate(daily_ratings.keys()):
  if bin_by_date[i] > 0:
    date_to_bucket[d] = dates_to_show[bin_by_date[i] - 1]

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

  aggregate_buckets = {d: {} for d in dates_to_show}

  for d in daily_ratings:
    if not d in date_to_bucket:
      continue
    bucket = date_to_bucket[d]
    for p in daily_ratings[d]:
      if p not in aggregate_buckets[bucket]:
        aggregate_buckets[bucket][p] = []
      aggregate_buckets[bucket][p].append(daily_ratings[d][p])

  aggregate_ratings = {d: {} for d in dates_to_show}
  for d in aggregate_buckets:
    for p in aggregate_buckets[d]:
      aggregate_ratings[d][p] = aggregate_values(aggregate_buckets[d][p], PLAYER_AGGREGATE)

  return aggregate_ratings

aggregate_ratings = get_aggregate_ratings(daily_ratings)
print(AGGREGATION_WINDOW + " aggregate ratings built for " \
                          + str(len(aggregate_ratings)) + " days")

for i, d in enumerate(dates_to_show):
  if d.year in SKIP_YEARS:
    del dates_to_show[i]
if dates_to_show[-1] == END_DATE:
  dates_to_show.pop()

metrics_bins = {}
ratio_stops = np.linspace(MIN_RATIO, MAX_RATIO, RATIO_BINS + 1)
actual_ratio_stops = ratio_stops[ : -1]
for r in actual_ratio_stops:
  metrics_bins[r] = []

if SHOW_BIN_COUNTS:
  print('\n=== Player count in each rating ratio bin ===')
  h = 'AGG START DATE'
  for b in actual_ratio_stops:
    h += '\t' + '{b:.2f}'.format(b = b)
  print(h)

player_counts_by_step = {}
player_periods = {}

for d in dates_to_show:
  ratings_in_range = {k: v for k, v in aggregate_ratings[d].items() \
                      if v >= THRESHOLD and v <= MAX_RATING}
  
  max_rating = max(ratings_in_range.values())

  bin_counts = [0] * len(ratio_stops)
  bin_players = []
  for r in ratio_stops:
    bin_players.append([])
  for p in ratings_in_range:
    rating = ratings_in_range[p]
    if p not in player_periods:
      player_periods[p] = 0
    player_periods[p] += 1
    if THRESHOLD_RELATIVE:
      rating_ratio = (rating - THRESHOLD) / (max_rating - THRESHOLD)
    else:
      rating_ratio = rating / max_rating
    if rating_ratio < ratio_stops[0]:
      continue
    for i, r in enumerate(ratio_stops):
      if rating_ratio < r:
        bin_counts[i - 1] += 1
        bin_players[i - 1].append(p)
        break
      if rating_ratio == r:
        bin_counts[i] += 1
        bin_players[i].append(p)
        break
  bin_counts[-2] += bin_counts[-1]
  bin_players[-2] += bin_players[-1]

  for i, r in enumerate(actual_ratio_stops):
    metrics_bins[r].append(bin_counts[i])

  for i, r in enumerate(actual_ratio_stops):
    for p in bin_players[i]:
      if p not in player_counts_by_step:
        player_counts_by_step[p] = {}
        for rs in actual_ratio_stops:
          player_counts_by_step[p][rs] = 0
      player_counts_by_step[p][r] += 1

  if BY_MEDAL_PERCENTAGES:
    for p in player_counts_by_step:
      for r in player_counts_by_step[p]:
        player_counts_by_step[p][r] = 100 * player_counts_by_step[p][r] / player_periods[p]

  if SHOW_BIN_COUNTS:
    s = str(d)
    for b in bin_counts[ : -1]:
      s += '\t' + str(b)
    print (s)


graph_metrics = {'outers': [], 'inners': [], 'lines': [], 'avgs': []}

def get_graph_metrics(data):
  outer_interval = {}
  outer_interval['start'] = np.percentile(data, 10, method = 'nearest')
  outer_interval['end'] = np.percentile(data, 90, method = 'nearest')
  outer_interval['width'] = outer_interval['end'] - outer_interval['start']
  inner_interval = {}
  inner_interval['start'] = np.percentile(data, 25, method = 'nearest')
  inner_interval['end'] = np.percentile(data, 75, method = 'nearest')
  inner_interval['width'] = inner_interval['end'] - inner_interval['start']
  line = (min(data), max(data))
  avg = np.average(data)

  return outer_interval, inner_interval, line, avg

cum_metrics_bins = {}
for r in actual_ratio_stops:
  cum_metrics_bins[r] = [0] * len(dates_to_show)

x_max_max = -1

last_r = -1
for r in reversed(actual_ratio_stops):
  for i, v in enumerate(metrics_bins[r]):
    if last_r == -1:
      cum_metrics_bins[r][i] = 0
    else:
      cum_metrics_bins[r][i] = cum_metrics_bins[last_r][i]
    cum_metrics_bins[r][i] += v
  last_r = r

  if GRAPH_CUMULATIVES:
    (outer, inner, line, avg) = get_graph_metrics(cum_metrics_bins[r])
  else:
    (outer, inner, line, avg) = get_graph_metrics(metrics_bins[r])

  if line[1] > x_max_max:
    x_max_max = line[1]

  graph_metrics['outers'].append(outer)
  graph_metrics['inners'].append(inner)
  graph_metrics['lines'].append(line)
  graph_metrics['avgs'].append(avg)

all_medals = AVG_MEDAL_CUMULATIVE_COUNTS.keys()
medal_indices = {medal: -1 for medal in all_medals}
for i, av in enumerate(graph_metrics['avgs']):
  for medal in medal_indices:
    if medal_indices[medal] == -1:
      medal_desired =  AVG_MEDAL_CUMULATIVE_COUNTS[medal]
      if av > medal_desired:
        if av - medal_desired > medal_desired - graph_metrics['avgs'][i - 1]:
          medal_indices[medal] = i - 1
        else:
          medal_indices[medal] = i

medal_thresholds = {}
for medal in all_medals:
  medal_thresholds[medal] = list(reversed(actual_ratio_stops))[medal_indices[medal]]

exp_nums = {}
for medal in all_medals:
  exp_nums[medal] = graph_metrics['avgs'][medal_indices[medal]]

print()
for medal in all_medals:
  print (medal + ':\t{m:.2f}'.format(m = medal_thresholds[medal]))


def readable_name(p):
  sep = p.find('_')
  return p[sep + 1 : ].split('.')[0].replace('_', ' ')

def country(p):
  return p.split('_')[0]

def full_readable_name(p):
  return readable_name(p) + ' (' + country(p) + ')'

player_medals = {}
for p in player_counts_by_step:
  if p not in player_medals:
    player_medals[p] = {medal: 0 for medal in all_medals}
  for r in sorted(player_counts_by_step[p].keys()):
    if r < medal_thresholds['bronze']:
      continue
    elif r < medal_thresholds['silver']:
      player_medals[p]['bronze'] += player_counts_by_step[p][r]
    elif r < medal_thresholds['gold']:
      player_medals[p]['silver'] += player_counts_by_step[p][r]
    else:
      player_medals[p]['gold'] += player_counts_by_step[p][r]

player_medals = dict(sorted(player_medals.items(),
                              key = lambda item: (item[1]['gold'], \
                                                  item[1]['silver'],
                                                  item[1]['bronze']), \
                              reverse = True))

if SHOW_TOP_PLAYERS:
  print('\n=== Top ' + str(TOP_PLAYERS) + ' Players ===')
  print('SPAN,\tMEDALS,\tGOLD,\tSILVER,\tBRONZE,\tPLAYER NAME')

  for i, p in enumerate(player_medals):
    s = str(player_periods[p]) + ','
    total_medals = sum(player_medals[p].values())
    if BY_MEDAL_PERCENTAGES:
      s += '\t{v:.2f}'.format(v = total_medals) + ','
    else:
      s += '\t' + str(total_medals) + ','
    for medal in ['gold', 'silver', 'bronze']:
      if BY_MEDAL_PERCENTAGES:
        s += '\t{v:.2f}'.format(v = player_medals[p][medal]) + ','
      else:
        s += '\t' + str(player_medals[p][medal]) + ','
    s += '\t' + full_readable_name(p)
    print (s)

    if i >= TOP_PLAYERS:
      break


def plot_medal_indicators(medal):
  medal_label = '{v:.2f}'.format(v = exp_nums[medal])
  plt.axhline(y = medal_thresholds[medal], linestyle = '--', linewidth = 1, \
                color = 'black', alpha = 0.8)
  plt.text(x = xmax - 1, y = medal_thresholds[medal], \
                s = medal.upper(), alpha = 0.8, fontsize = 'large', \
                horizontalalignment = 'right', verticalalignment = 'bottom')
  medal_ymax_ratio = (medal_thresholds[medal] - ymin) / (ymax - ymin)
  plt.axvline(x = exp_nums[medal], linestyle = ':', linewidth = 1, \
                color = 'black', alpha = 0.8, ymax = medal_ymax_ratio)

if SHOW_GRAPH:
  from matplotlib import pyplot as plt

  resolution = tuple([7.2, 7.2])
  fig, ax = plt.subplots(figsize = resolution)

  TITLE_TEXT = "No. of players above ratio vs top player rating\n " \
                + FORMAT + ' ' + TYPE + ' (' + str(START_DATE) \
                          + ' to ' + str(END_DATE) + ')'
  ax.set_title(TITLE_TEXT, fontsize ='xx-large')

  ylabel = 'Rating ratio (' + AGGREGATION_WINDOW + ' ' + PLAYER_AGGREGATE + ')'
  ax.set_ylabel(ylabel, fontsize ='x-large')
  ax.set_xlabel('No. of players above ratio threshold', fontsize ='x-large')

  ymin = MIN_RATIO - RATIO_STEP
  ymax = MAX_RATIO
  ax.set_ylim(ymin, ymax)
  ax.set_yticks(actual_ratio_stops)
  ax.set_yticklabels(['{v:.2f}'.format(v = r) for r in actual_ratio_stops], \
                          fontsize ='medium')

  xmax = x_max_max + 1
  ax.set_xlim(0, xmax)
  xticks = list(range(0, xmax + 1, 1))
  ax.set_xticks(xticks)

  xlabwidth = 1
  if xmax > 25:
    xlabwidth = 2
  if xmax > 50:
    xlabwidth = 5
  if xmax > 100:
    xlabwidth = 10
  xticklabels = [str(x) if x % xlabwidth == 0 else '' for x in xticks]
  ax.set_xticklabels(xticklabels, fontsize ='medium')

  ax.grid(True, which = 'both', axis = 'x', alpha = 0.5)

  outer_starts = [interval['start'] for interval in graph_metrics['outers']]
  outer_widths = [interval['width'] for interval in graph_metrics['outers']]
  ax.barh(y = list(reversed(actual_ratio_stops)), width = outer_widths, \
            align = 'center', height = 0.9 * RATIO_STEP, left = outer_starts, \
            color = 'darkgrey', alpha = 0.4, \
          )

  inner_starts = [interval['start'] for interval in graph_metrics['inners']]
  inner_widths = [interval['width'] for interval in graph_metrics['inners']]
  ax.barh(y = list(reversed(actual_ratio_stops)), width = inner_widths, \
          align = 'center', height = 0.8 * RATIO_STEP, left = inner_starts, \
          color = 'green', alpha = 0.5, \
        )
  
  plt.plot(graph_metrics['avgs'], list(reversed(actual_ratio_stops)), \
                    linewidth = 0, alpha = 0.5, \
                    marker = 'x', markeredgecolor = 'blue', \
                    markersize = 8, markeredgewidth = 2)
  
  for i, r in enumerate(reversed(actual_ratio_stops)):
    plt.plot(list(graph_metrics['lines'][i]), [r, r], linewidth = 2, \
                      color = 'black', alpha = 0.9, \
                      marker = 'o', markerfacecolor = 'red', \
                      markersize = 3, markeredgewidth = 0)

  for medal in all_medals:
    plot_medal_indicators(medal)

  fig.tight_layout()
  plt.show()
