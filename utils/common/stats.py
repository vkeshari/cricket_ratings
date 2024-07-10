from scipy.optimize import curve_fit

import numpy as np


def get_stats_for_list(values, stat_type):
  assert stat_type in ['avg', 'median', 'min', 'max', 'first', 'last', \
                      'p10', 'p20', 'p25', 'p50', 'p75', 'p80', 'p90'], \
        "Invalid stat_type provided"

  if not values:
    return 0

  if stat_type == 'avg':
    return np.average(values)
  if stat_type == 'min':
    return min(values)
  if stat_type == 'max':
    return max(values)
  if stat_type == 'first':
    return values[0]
  if stat_type == 'last':
    return values[-1]

  if stat_type == 'p10':
    return np.percentile(values, 10, method = 'nearest')
  if stat_type == 'p20':
    return np.percentile(values, 20, method = 'nearest')
  if stat_type == 'p25':
    return np.percentile(values, 25, method = 'nearest')
  if stat_type == 'p50' or stat_type == 'median':
    return np.percentile(values, 50, method = 'nearest')
  if stat_type == 'p75':
    return np.percentile(values, 75, method = 'nearest')
  if stat_type == 'p80':
    return np.percentile(values, 80, method = 'nearest')
  if stat_type == 'p90':
    return np.percentile(values, 90, method = 'nearest')


def normalize_array(values, normalize_to = 100):
  sum_values = sum(values)
  return [v * normalize_to / sum_values for v in values]


def exp_func(x, a, b):
  return a * np.exp(-x / b)

def fit_exp_curve(xs, ys, xs_new = [], xs_range = (0, 1)):
  xs_scaled = [(x - xs_range[0]) / (xs_range[1] - xs_range[0]) for x in xs]
  xs_new_scaled = [(x - xs_range[0]) / (xs_range[1] - xs_range[0]) for x in xs_new]
  (a, b), cov = curve_fit(exp_func, xs_scaled, ys)
  ys_new = [exp_func(x, a, b) for x in xs_new_scaled]
  exp_mean = xs_range[0] + b * (xs_range[1] - xs_range[0])
  return ys_new, exp_mean, cov

