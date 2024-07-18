from fitter import Fitter
from scipy.optimize import curve_fit
from sklearn.preprocessing import power_transform

import numpy as np

VALID_STATS = {'avg', 'std', 'median', 'min', 'max', 'first', 'last', \
                      'p10', 'p20', 'p25', 'p50', 'p75', 'p80', 'p90'}


def get_stats_for_list(values, stat_type):
  assert stat_type in VALID_STATS, "Invalid stat_type provided"

  if not values:
    return 0

  if stat_type == 'avg':
    return np.average(values)
  if stat_type == 'std':
    return np.std(values)
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
  if len(values) == 0:
    return []
    
  sum_values = sum(values)
  if sum_values == 0:
    return [0] * len(values)
    
  return [v * normalize_to / sum_values for v in values]


def sample_from_distribution(bin_counts, bins, bin_width, \
                              val_range = (0, 1), scale_bins = 1):
  all_vals = []
  rng = np.random.default_rng()
  for i, b in enumerate(bins):
    vals = rng.integers(low = b, high = b + bin_width, \
                        size = round(bin_counts[i] * scale_bins))
    scaled_vals = [(v - val_range[0]) / (val_range[1] - val_range[0]) for v in vals]
    all_vals.append(scaled_vals)
  all_vals = np.concatenate(all_vals)

  return all_vals


def make_distribution_normal(bin_counts, bins, bin_width, val_range, scale_bins):
  sampled_vals = sample_from_distribution(bin_counts, bins, bin_width, \
                                          val_range, scale_bins)
  
  normalized = power_transform(sampled_vals.reshape(-1, 1)).reshape(1, -1).flatten()
  normalized = [val_range[0] + v * (val_range[1] - val_range[0]) for v in normalized]
  
  hist_bins = bins + [bins[-1] + bin_width]
  dist = np.histogram(normalized, bins = hist_bins)[0]
  dist = normalize_array(dist)
  
  assert len(bin_counts) == len(dist), \
          "Mismatch in no. of bins after normalization: {v1} vs {v2}" \
                  .format(v1 = len(bin_counts), v2 = len(dist))

  return dist


def fit_dist_to_hist(bin_counts, bins, bin_width, val_range, scale_bins):
  sampled_vals = sample_from_distribution(bin_counts, bins, bin_width, \
                                          val_range, scale_bins)

  fit = Fitter(sampled_vals)
  fit.fit()
  print ("Fit complete!")

  print(fit.summary(Nbest = 50, method = 'ks_statistic'))
  return fit


def exp_func(x, a, b):
  return a * np.exp(-x / b)

def fit_exp_curve(xs, ys, xs_new = [], xs_range = (0, 1)):
  xs_scaled = [(x - xs_range[0]) / (xs_range[1] - xs_range[0]) for x in xs]
  xs_new_scaled = [(x - xs_range[0]) / (xs_range[1] - xs_range[0]) for x in xs_new]
  (a, b), cov = curve_fit(exp_func, xs_scaled, ys)
  ys_new = [exp_func(x, a, b) for x in xs_new_scaled]
  exp_mean = xs_range[0] + b * (xs_range[1] - xs_range[0])
  return ys_new, exp_mean, cov

