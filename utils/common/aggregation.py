import numpy as np

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
                                        and d.year % 10 == 1


def aggregate_values(values, agg_type):
  assert agg_type in ['avg', 'median', 'min', 'max', 'first', 'last']

  if not values:
    return 0

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
