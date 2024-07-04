from common.aggregation import aggregate_values, \
                                get_aggregate_ratings, \
                                is_aggregation_window_start
from common.data import get_daily_ratings
from common.output import string_to_date, readable_name_and_country

from datetime import date, timedelta

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
THRESHOLD = 500
MAX_RATING = 1000
RATING_STEP = 20

# ['', 'rating', 'rank', 'either', 'both']
CHANGED_DAYS_CRITERIA = 'rating'

# Aggregation
# ['', 'monthly', 'quarterly', 'halfyearly', 'yearly', 'decadal']
AGGREGATION_WINDOW = 'yearly'
# ['', 'avg', 'median', 'min', 'max', 'first', 'last']
PLAYER_AGGREGATE = 'max'

GRAPH_CUMULATIVES = True
BY_MEDAL_PERCENTAGES = False
CHANGED_DAYS_ONLY = True

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
assert RATING_STEP >= 10, "RATING_STEP must be at least 10"

assert CHANGED_DAYS_CRITERIA in ['', 'rating', 'rank', 'either', 'both']

assert AGGREGATION_WINDOW in ['monthly', 'quarterly', 'halfyearly', 'yearly', 'decadal'], \
      "Invalid AGGREGATION_WINDOW provided"
assert PLAYER_AGGREGATE in ['avg', 'median', 'min', 'max', 'first', 'last'], \
      "Invalid PLAYER_AGGREGATE provided"

assert not set(AVG_MEDAL_CUMULATIVE_COUNTS.keys()) - {'gold', 'silver', 'bronze'}, \
    'AVG_MEDAL_CUMULATIVE_COUNTS keys must be gold silver and bronze'
for amcc in AVG_MEDAL_CUMULATIVE_COUNTS.values():
  assert amcc > 0, "All values in AVG_MEDAL_CUMULATIVE_COUNTS must be positive"

assert TOP_PLAYERS > 5, "TOP_PLAYERS must be at least 5"

print (FORMAT + '\t' + TYPE)
print (str(START_DATE) + ' to ' + str(END_DATE))
print (str(THRESHOLD) + ' : ' + str(MAX_RATING))
print (AGGREGATION_WINDOW + ' / ' + PLAYER_AGGREGATE)

daily_ratings, _ = get_daily_ratings(TYPE, FORMAT, \
                          changed_days_criteria = CHANGED_DAYS_CRITERIA, \
                          agg_window = AGGREGATION_WINDOW, \
                          allrounders_geom_mean = ALLROUNDERS_GEOM_MEAN)

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

aggregate_ratings = get_aggregate_ratings(daily_ratings, agg_dates = dates_to_show, \
                                          date_to_agg_date = date_to_bucket, \
                                          aggregation_window = AGGREGATION_WINDOW, \
                                          player_aggregate = PLAYER_AGGREGATE)

for i, d in enumerate(dates_to_show):
  if d.year in SKIP_YEARS:
    del dates_to_show[i]
if dates_to_show[-1] == END_DATE:
  dates_to_show.pop()

metrics_bins = {}
rating_stops = list(range(THRESHOLD, MAX_RATING, RATING_STEP))
actual_rating_stops = rating_stops[ : -1]
for r in actual_rating_stops:
  metrics_bins[r] = []

if SHOW_BIN_COUNTS:
  print('\n=== Player count in each rating bin ===')
  h = 'AGG START DATE'
  for b in actual_rating_stops:
    h += '\t' + str(b)
  print(h)

player_counts_by_step = {}
player_periods = {}

for d in dates_to_show:
  ratings_in_range = {k: v for k, v in aggregate_ratings[d].items() \
                      if v >= THRESHOLD and v <= MAX_RATING}

  bin_counts = [0] * len(rating_stops)
  bin_players = []
  for r in rating_stops:
    bin_players.append([])
  for p in ratings_in_range:
    rating = ratings_in_range[p]
    if p not in player_periods:
      player_periods[p] = 0
    player_periods[p] += 1
    if rating < rating_stops[0]:
      continue
    for i, r in enumerate(rating_stops):
      if rating < r:
        bin_counts[i - 1] += 1
        bin_players[i - 1].append(p)
        break
      if rating == r:
        bin_counts[i] += 1
        bin_players[i].append(p)
        break
  bin_counts[-2] += bin_counts[-1]
  bin_players[-2] += bin_players[-1]

  for i, r in enumerate(actual_rating_stops):
    metrics_bins[r].append(bin_counts[i])

  for i, r in enumerate(actual_rating_stops):
    for p in bin_players[i]:
      if p not in player_counts_by_step:
        player_counts_by_step[p] = {}
        for rs in actual_rating_stops:
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
for r in actual_rating_stops:
  cum_metrics_bins[r] = [0] * len(dates_to_show)

x_max_max = -1

last_r = -1
for r in reversed(actual_rating_stops):
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
  medal_thresholds[medal] = list(reversed(actual_rating_stops))[medal_indices[medal]]

exp_nums = {}
for medal in all_medals:
  exp_nums[medal] = graph_metrics['avgs'][medal_indices[medal]]

print()
for medal in all_medals:
  print (medal + ':\t{m:.2f}'.format(m = medal_thresholds[medal]))


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
    s += '\t' + readable_name_and_country(p)
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
  medal_ymax_rating = (medal_thresholds[medal] - ymin) / (ymax - ymin)
  plt.axvline(x = exp_nums[medal], linestyle = ':', linewidth = 1, \
                color = 'black', alpha = 0.8, ymax = medal_ymax_rating)

if SHOW_GRAPH:
  from matplotlib import pyplot as plt

  resolution = tuple([7.2, 7.2])
  fig, ax = plt.subplots(figsize = resolution)

  TITLE_TEXT = "No. of players above rating\n " \
                + FORMAT + ' ' + TYPE + ' (' + str(START_DATE) \
                          + ' to ' + str(END_DATE) + ')'
  ax.set_title(TITLE_TEXT, fontsize ='xx-large')

  ylabel = 'Rating (' + AGGREGATION_WINDOW + ' ' + PLAYER_AGGREGATE + ')'
  ax.set_ylabel(ylabel, fontsize ='x-large')
  ax.set_xlabel('No. of players above rating', fontsize ='x-large')

  ymin = THRESHOLD - RATING_STEP
  ymax = MAX_RATING
  ax.set_ylim(ymin, ymax)
  ax.set_yticks(actual_rating_stops)
  ax.set_yticklabels([str(r) for r in actual_rating_stops], \
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
  ax.barh(y = list(reversed(actual_rating_stops)), width = outer_widths, \
            align = 'center', height = 0.9 * RATING_STEP, left = outer_starts, \
            color = 'darkgrey', alpha = 0.4, \
          )

  inner_starts = [interval['start'] for interval in graph_metrics['inners']]
  inner_widths = [interval['width'] for interval in graph_metrics['inners']]
  ax.barh(y = list(reversed(actual_rating_stops)), width = inner_widths, \
          align = 'center', height = 0.8 * RATING_STEP, left = inner_starts, \
          color = 'green', alpha = 0.5, \
        )
  
  plt.plot(graph_metrics['avgs'], list(reversed(actual_rating_stops)), \
                    linewidth = 0, alpha = 0.5, \
                    marker = 'x', markeredgecolor = 'blue', \
                    markersize = 8, markeredgewidth = 2)
  
  for i, r in enumerate(reversed(actual_rating_stops)):
    plt.plot(list(graph_metrics['lines'][i]), [r, r], linewidth = 2, \
                      color = 'black', alpha = 0.9, \
                      marker = 'o', markerfacecolor = 'red', \
                      markersize = 3, markeredgewidth = 0)

  for medal in all_medals:
    plot_medal_indicators(medal)

  fig.tight_layout()
  plt.show()
