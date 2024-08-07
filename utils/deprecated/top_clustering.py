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
START_DATE = date(2021, 1, 1)
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


from sklearn.mixture import GaussianMixture
from sklearn.neighbors import KernelDensity

from matplotlib import pyplot as plt

def fit_kde(day_ratings, rating_range, xmax):
  bins = 50
  fig, ax = plt.subplots()
  ax.set_xlim(THRESHOLD, xmax)
  ax.set_ylim(-20, 20)
  ax.grid(True)
  plt.hist(day_ratings, bins = bins)

  bandwidth = (MAX_RATING - THRESHOLD) / bins

  for kernel in {'gaussian', 'exponential', 'epanechnikov'} :
    kde = KernelDensity(kernel = kernel, bandwidth = bandwidth) \
                    .fit(day_ratings.reshape(-1, 1))

    estimates = kde.score_samples(rating_range.reshape(-1, 1))
    plt.plot(rating_range, estimates, label = kernel, alpha = 0.5, linewidth = 2)

  ax.legend()
  fig.tight_layout()
  plt.show()

def fit_gmm(day_ratings, rating_range, xmax):
  bins = 10
  fig, ax = plt.subplots()
  ax.set_xlim(THRESHOLD, xmax)
  ax.set_ylim(0, 100)
  ax.grid(True)
  plt.hist(day_ratings, bins = bins)

  #weights = [(i + 1) for i in range(bins)]
  #weights = weights / np.linalg.norm(weights, ord = 1)
  gm = GaussianMixture(n_components = bins)
  gme = gm.fit(day_ratings.reshape(-1, 1))

  print(gme.means_)
  estimates = gme.predict(rating_range.reshape(-1, 1))
  plt.plot(rating_range, estimates, alpha = 0.5, linewidth = 2)

  fig.tight_layout()
  plt.show()


for d in dates_to_show:
  day_ratings = np.array([v for v in aggregate_ratings[d].values() if v >= THRESHOLD])
  xmax = max(day_ratings) + 50
  rating_range = np.array(range(THRESHOLD, xmax))

  fit_kde(day_ratings, rating_range, xmax)
  # fit_gmm(day_ratings, rating_range, xmax)
  