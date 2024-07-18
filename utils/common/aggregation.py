from common.stats import get_stats_for_list, normalize_array, fit_exp_curve, VALID_STATS

from datetime import date, timedelta

import numpy as np

ONE_DAY = timedelta(days = 1)
LAST_FUTURE_DATE = date(2030, 1, 1)

VALID_AGGREGATIONS = {'', 'monthly', 'quarterly', 'halfyearly', \
                            'yearly', 'fiveyearly', 'decadal', '1952_1992'}

def is_aggregation_window_start(d, agg_window):
  assert agg_window in VALID_AGGREGATIONS, "Invalid agg_window provided"

  if not agg_window:
    return True

  return agg_window == 'monthly' and d.day == 1 \
      or agg_window == 'quarterly' and d.day == 1 and d.month in [1, 4, 7, 10] \
      or agg_window == 'halfyearly' and d.day == 1 and d.month in [1, 7] \
      or agg_window == 'yearly' and d.day == 1 and d.month == 1 \
      or agg_window == 'fiveyearly' and d.day == 1 and d.month == 1 \
                                        and d.year % 5 == 0 \
      or agg_window == 'decadal' and d.day == 1 and d.month == 1 \
                                        and d.year % 10 == 0 \
      or agg_window == '1952_1992' and d.day == 1 and d.month == 1 \
                                        and d.year in {1952, 1992}


def get_next_aggregation_window_start(d, agg_window):
  assert agg_window in VALID_AGGREGATIONS, "Invalid agg_window provided"

  next_d = d + ONE_DAY
  while not is_aggregation_window_start(next_d, agg_window):
    next_d += ONE_DAY
    assert next_d < LAST_FUTURE_DATE, "No next aggregation date found after " + str(d)
  return next_d


def date_to_aggregation_date(dates, aggregation_dates):
  bin_by_date = np.searchsorted(aggregation_dates, dates, side = 'right')
  date_to_aggregation_date = {}
  for i, d in enumerate(dates):
    if bin_by_date[i] > 0:
      date_to_aggregation_date[d] = aggregation_dates[bin_by_date[i] - 1]
  return date_to_aggregation_date


def get_aggregation_dates(daily_ratings, agg_window, start_date, end_date):
  assert agg_window in VALID_AGGREGATIONS, "Invalid agg_window provided"

  first_date = min(daily_ratings.keys())
  last_date = max(daily_ratings.keys())

  aggregation_dates = []
  d = first_date
  while d <= last_date:
    if d >= start_date and d <= end_date and is_aggregation_window_start(d, agg_window):
      aggregation_dates.append(d)
    d += ONE_DAY

  return aggregation_dates


def get_aggregate_ratings(daily_ratings, agg_dates, date_to_agg_date, player_aggregate):
  assert player_aggregate in VALID_STATS, "Invalid player_aggregate provided"

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
      aggregate_ratings[d][p] = get_stats_for_list(aggregate_buckets[d][p], \
                                                      stat_type = player_aggregate)
  
  print("Aggregate ratings built for " + str(len(aggregate_ratings)) + " days")

  return aggregate_ratings


def get_aggregated_distribution(daily_ratings, agg_dates, date_to_agg_date, \
                                dist_aggregate, bin_stops, normalize_to = 100, \
                                ignore_zero_ratings = True):
  assert dist_aggregate in VALID_STATS, "Invalid dist_aggregate provided"

  aggregate_buckets = {d: [] for d in agg_dates}
  for d in daily_ratings:
    if not d in date_to_agg_date:
      continue
    bucket = date_to_agg_date[d]
    if not bucket in agg_dates:
      continue
    ratings_for_day = list(daily_ratings[d].values())
    if ignore_zero_ratings:
      ratings_for_day = [r for r in ratings_for_day if r > 0]
    distribution_for_date = np.histogram(ratings_for_day, bins = bin_stops)[0]
    aggregate_buckets[bucket].append(distribution_for_date)

  for d in aggregate_buckets:
    for i, dist in enumerate(aggregate_buckets[d]):
      aggregate_buckets[d][i] = normalize_array(dist, normalize_to)

  aggregated_buckets = {d: [] for d in agg_dates}
  num_bins = len(bin_stops) - 1

  for d in aggregate_buckets:
    aggregate_buckets[d] = list(zip(*aggregate_buckets[d]))

  for d in aggregate_buckets:
    if len(aggregate_buckets[d]) == 0:
      aggregated_buckets[d] = [0] * num_bins
      continue
    for i in range(num_bins):
      aggregated_buckets[d].append(get_stats_for_list(aggregate_buckets[d][i], \
                                                      stat_type = dist_aggregate))

  return aggregated_buckets, bin_stops


def get_single_window_distribution(daily_ratings, agg_date, agg_window, agg_type, \
                                    threshold, max_rating, bin_size, \
                                    get_percentiles = [], fit_curve = False):
  next_d = get_next_aggregation_window_start(agg_date, agg_window)

  date_to_agg_date = {d: agg_date for d in daily_ratings \
                              if d >= agg_date and d < next_d}
  bin_stops = list(range(threshold, max_rating, bin_size)) + [max_rating]

  aggregated_buckets, bins = get_aggregated_distribution(daily_ratings, \
                                    agg_dates = [agg_date], \
                                    date_to_agg_date = date_to_agg_date, \
                                    dist_aggregate = agg_type, \
                                    bin_stops = bin_stops)

  bin_counts = normalize_array(aggregated_buckets[agg_date])
  actual_bins = bins[ : -1]

  if get_percentiles or fit_curve:
    stats_bin_size = (max_rating - threshold) / 100
    stats_bin_stops = np.linspace(threshold, max_rating, 101)
    stats_buckets, stats_bins = get_aggregated_distribution(daily_ratings, \
                                    agg_dates = [agg_date], \
                                    date_to_agg_date = date_to_agg_date, \
                                    dist_aggregate = agg_type, \
                                    bin_stops = stats_bin_stops)

    stats_bin_counts = normalize_array(stats_buckets[agg_date])
    stats_bins = stats_bins[ : -1]

  all_percentiles = {}
  if get_percentiles:
    for p in get_percentiles:
      cum_sum = 0
      for i, b in enumerate(stats_bins):
        cum_sum += stats_bin_counts[i]
        if cum_sum >= p:
          all_percentiles[p] = b
          break
      if p not in all_percentiles:
        all_percentiles[p] = threshold

  xs_fit, ys_fit, fit_mean = [], [], 0
  if fit_curve:
    xs_fit = range(threshold, max_rating)
    ys_fit, exp_mean, cov = fit_exp_curve(xs = stats_bins, ys = stats_bin_counts, \
                                          xs_new = xs_fit, \
                                          xs_range = (threshold, max_rating))
    ys_fit = [y * (bin_size / stats_bin_size) for y in ys_fit]
    fit_mean = round(exp_mean)
    print("Exp mean: " + str(fit_mean))

  return bin_counts, actual_bins, all_percentiles, (xs_fit, ys_fit, fit_mean)



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
