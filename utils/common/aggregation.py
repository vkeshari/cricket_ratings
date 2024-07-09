import numpy as np

from datetime import timedelta

ONE_DAY = timedelta(days = 1)


def is_aggregation_window_start(d, agg_window):
  assert agg_window in ['', 'monthly', 'quarterly', 'halfyearly', 'yearly', 'decadal'], \
        "Invalid agg_window provided"

  if not agg_window:
    return True

  return agg_window == 'monthly' and d.day == 1 \
      or agg_window == 'quarterly' and d.day == 1 and d.month in [1, 4, 7, 10] \
      or agg_window == 'halfyearly' and d.day == 1 and d.month in [1, 7] \
      or agg_window == 'yearly' and d.day == 1 and d.month == 1 \
      or agg_window == 'decadal' and d.day == 1 and d.month == 1 \
                                        and d.year % 10 == 0


def get_next_aggregation_window_start(d, agg_window):
  assert agg_window in ['', 'monthly', 'quarterly', 'halfyearly', 'yearly', 'decadal'], \
        "Invalid agg_window provided"

  next_d = d + ONE_DAY
  while not is_aggregation_window_start(next_d, agg_window):
    next_d += ONE_DAY
  return next_d


def date_to_aggregation_date(dates, aggregation_dates):
  bin_by_date = np.searchsorted(aggregation_dates, dates, side = 'right')
  date_to_aggregation_date = {}
  for i, d in enumerate(dates):
    if bin_by_date[i] > 0:
      date_to_aggregation_date[d] = aggregation_dates[bin_by_date[i] - 1]
  return date_to_aggregation_date


def aggregate_values(values, agg_type):
  assert agg_type in ['avg', 'median', 'min', 'max', 'first', 'last', \
                      'p10', 'p20', 'p25', 'p50', 'p75', 'p80', 'p90'], \
        "Invalid agg_type provided"

  if not values:
    return 0

  if agg_type == 'avg':
    return np.average(values)
  if agg_type == 'min':
    return min(values)
  if agg_type == 'max':
    return max(values)
  if agg_type == 'first':
    return values[0]
  if agg_type == 'last':
    return values[-1]

  if agg_type == 'p10':
    return np.percentile(values, 10, method = 'nearest')
  if agg_type == 'p20':
    return np.percentile(values, 20, method = 'nearest')
  if agg_type == 'p25':
    return np.percentile(values, 25, method = 'nearest')
  if agg_type == 'p50' or agg_type == 'median':
    return np.percentile(values, 50, method = 'nearest')
  if agg_type == 'p75':
    return np.percentile(values, 75, method = 'nearest')
  if agg_type == 'p80':
    return np.percentile(values, 80, method = 'nearest')
  if agg_type == 'p90':
    return np.percentile(values, 90, method = 'nearest')


def get_aggregate_ratings(daily_ratings, agg_dates, date_to_agg_date, \
                          aggregation_window, player_aggregate):
  assert aggregation_window in ['monthly', 'quarterly', 'halfyearly', \
                                    'yearly', 'decadal'], \
        "Invalid aggregation_window provided"
  assert player_aggregate in ['avg', 'median', 'min', 'max', 'first', 'last'], \
        "Invalid player_aggregate provided"

  aggregate_buckets = {d: {} for d in agg_dates}

  for d in daily_ratings:
    if d not in date_to_agg_date:
      continue
    bucket = date_to_agg_date[d]
    for p in daily_ratings[d]:
      if p not in aggregate_buckets[bucket]:
        aggregate_buckets[bucket][p] = []
      aggregate_buckets[bucket][p].append(daily_ratings[d][p])

  aggregate_ratings = {d: {} for d in agg_dates}
  for d in aggregate_buckets:
    for p in aggregate_buckets[d]:
      aggregate_ratings[d][p] = aggregate_values(aggregate_buckets[d][p], player_aggregate)
  
  print(aggregation_window + " aggregate ratings built for " \
                            + str(len(aggregate_ratings)) + " days")

  return aggregate_ratings


def get_aggregated_distribution(daily_ratings, agg_dates, date_to_agg_date, \
                                dist_aggregate, bin_stops, normalize_to = 100, \
                                ignore_zero_ratings = True):
  assert dist_aggregate in ['avg', 'median', 'min', 'max', 'first', 'last'], \
        "Invalid dist_aggregate provided"

  aggregate_buckets = {d: [] for d in agg_dates}
  for d in daily_ratings:
    if not d in date_to_agg_date:
      continue
    bucket = date_to_agg_date[d]
    ratings_for_day = list(daily_ratings[d].values())
    if ignore_zero_ratings:
      ratings_for_day = [r for r in ratings_for_day if r > 0]
    distribution_for_date = np.histogram(ratings_for_day, bins = bin_stops)[0]
    aggregate_buckets[bucket].append(distribution_for_date)

  for d in aggregate_buckets:
    for dist in aggregate_buckets[d]:
      total_count = sum(dist)
      for i, val in enumerate(dist):
        dist[i] = val * normalize_to / total_count

  aggregated_buckets = {d: [] for d in agg_dates}
  num_bins = len(bin_stops) - 1

  for d in aggregate_buckets:
    aggregate_buckets[d] = list(zip(*aggregate_buckets[d]))

  for d in aggregate_buckets:
    for i in range(num_bins):
      aggregated_buckets[d].append( \
                aggregate_values(aggregate_buckets[d][i], dist_aggregate))

  return aggregated_buckets, bin_stops


def get_metrics_by_stops(aggregate_ratings, stops, dates, \
                            by_percentage = False, show_bin_counts = False):
  assert not set(dates) - aggregate_ratings.keys(), \
          "Not all dates are present in aggregate_ratings"

  actual_stops = stops[ : -1]
  metrics_bins = {s : [] for s in actual_stops}

  if show_bin_counts:
    print('\n=== Player count in each bin ===')
    h = 'AGG START DATE'
    for b in actual_stops:
      h += '\t' + '{b:.2f}'.format(b = b)
    h += '\tTOTAL'
    print(h)

  player_counts_by_step = {}
  player_periods = {}

  for d in dates:
    bin_counts = {s: 0 for s in actual_stops}
    ratings_in_range = {k: v for k, v in aggregate_ratings[d].items() \
                            if v >= stops[0] and v <= stops[-1]}

    values = list(ratings_in_range.values())
    value_to_bin = np.searchsorted(a = stops, v = values, side = 'right')
    value_to_bin = [v - 1 for v in value_to_bin]

    for i, p in enumerate(ratings_in_range.keys()):
      player_bin = int(value_to_bin[i])
      if player_bin < 0 or player_bin > len(actual_stops):
        continue
      if player_bin == len(actual_stops):
        player_bin = len(actual_stops) - 1
      player_bin_stop = actual_stops[player_bin]
      bin_counts[player_bin_stop] += 1

      if p not in player_counts_by_step:
        player_counts_by_step[p] = {s: 0 for s in actual_stops}
      player_counts_by_step[p][player_bin_stop] += 1

      if p not in player_periods:
        player_periods[p] = 0
      player_periods[p] += 1

    for s in actual_stops:
      metrics_bins[s].append(bin_counts[s])

    if show_bin_counts:
      s = str(d)
      for b in bin_counts:
        s += '\t' + str(bin_counts[b])
      s += '\t' + str(sum(bin_counts.values()))
      print (s)

  if by_percentage:
    for p in player_counts_by_step:
      for s in player_counts_by_step[p]:
        player_counts_by_step[p][s] = 100 * player_counts_by_step[p][s] / player_periods[p]

  return metrics_bins, player_counts_by_step, player_periods
