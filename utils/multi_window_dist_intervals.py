from common.aggregation import is_aggregation_window_start, \
                                get_aggregation_dates, date_to_aggregation_date, \
                                get_aggregated_distribution, VALID_AGGREGATIONS
from common.data import get_daily_ratings
from common.interval_metrics import get_graph_metrics
from common.interval_graph import plot_interval_graph
from common.stats import normalize_array, make_distribution_normal, VALID_STATS

from datetime import date
from pathlib import Path

# ['', 'batting', 'bowling', 'allrounder']
TYPE = ''
# ['', 'test', 'odi', 't20']
FORMAT = 't20'

START_DATE = date(2011, 1, 1)
END_DATE = date(2024, 7, 1)
SKIP_YEARS = list(range(1915, 1920)) + list(range(1940, 1946)) + [2020]

# Upper and lower bounds of ratings to show
THRESHOLD = 500
MAX_RATING = 1000
BIN_SIZE = 20

# See common.aggregation.VALID_AGGREGATIONS for possible windows
AGGREGATION_WINDOW = 'yearly'
# See common.stats.VALID_STATS for possible aggregate stats
BIN_AGGREGATE = 'avg'

# ['', 'rating', 'rank', 'either', 'both']
CHANGED_DAYS_CRITERIA = 'rating'

SHOW_BIN_COUNTS = False
SHOW_GRAPH = True
GRAPH_CUMULATIVES = True
TRIM_EMPTY_ROWS = True
HIDE_THRESHOLD = False
TRIM_GRAPH_TO = 0

RESCALE = True

# Alternate way to calculate allrounder ratings. Use geometric mean of batting and bowling.
ALLROUNDERS_GEOM_MEAN = True

if TYPE:
  assert TYPE in ['batting', 'bowling', 'allrounder'], "Invalid TYPE provided"
if FORMAT:
  assert FORMAT in ['test', 'odi', 't20'], "Invalid FORMAT provided"
assert START_DATE < END_DATE, "START_DATE must be earlier than END_DATE"
assert END_DATE <= date.today(), "Future END_DATE requested"

assert MAX_RATING <= 1000, "MAX_RATING must not be greater than 1000"
assert THRESHOLD >= 0 and THRESHOLD < MAX_RATING, \
      "THRESHOLD must be between 0 and MAX_RATING"
assert (MAX_RATING - THRESHOLD) % 100 == 0, "Range of ratings must be a multiple of 100"

assert CHANGED_DAYS_CRITERIA in ['', 'rating', 'rank', 'either', 'both']

assert BIN_SIZE >= 10 and BIN_SIZE <= 100, "BIN_SIZE should be between 10 and 100"
assert (MAX_RATING - THRESHOLD) % BIN_SIZE == 0, \
      "BIN_SIZE should be a factor of ratings range"

assert AGGREGATION_WINDOW in VALID_AGGREGATIONS, "Invalid AGGREGATION_WINDOW provided"
assert BIN_AGGREGATE in VALID_STATS, "Invalid BIN_AGGREGATE provided"

if TRIM_EMPTY_ROWS or GRAPH_CUMULATIVES or TRIM_GRAPH_TO:
  assert SHOW_GRAPH, "TRIM_EMPTY_ROWS, GRAPH_CUMULATIVES  or TRIM_GRAPH_TO set " \
                        + "but SHOW_GRAPH not set"

types_and_formats = []
if TYPE and FORMAT:
  types_and_formats.append((TYPE, FORMAT))
elif TYPE:
  for f in ['test', 'odi', 't20']:
    types_and_formats.append((TYPE, f))
elif FORMAT:
  for t in ['batting', 'bowling']:
    types_and_formats.append((t, FORMAT))
else:
  for f in ['test', 'odi', 't20']:
    for t in ['batting', 'bowling']:
      types_and_formats.append((t, f))

for typ, frmt in types_and_formats:
  print (frmt + ' : ' + typ)
  print (str(THRESHOLD) + ' : ' + str(BIN_SIZE) + ' : ' + str(MAX_RATING))

  daily_ratings, _ = get_daily_ratings(typ, frmt, \
                            changed_days_criteria = CHANGED_DAYS_CRITERIA, \
                            allrounders_geom_mean = ALLROUNDERS_GEOM_MEAN)

  aggregation_dates = get_aggregation_dates(daily_ratings, \
                                            agg_window = AGGREGATION_WINDOW, \
                                            start_date = START_DATE, end_date = END_DATE)

  date_to_agg_date = date_to_aggregation_date(list(daily_ratings.keys()), \
                                              aggregation_dates)

  bin_stops = range(THRESHOLD, MAX_RATING + 1, BIN_SIZE)
  actual_bin_stops = list(bin_stops)[ : -1]

  aggregation_dates = list(filter(lambda d: d.year not in SKIP_YEARS, aggregation_dates))
  if aggregation_dates[-1] == END_DATE:
    aggregation_dates.pop()

  aggregated_buckets, _ = get_aggregated_distribution(daily_ratings, \
                                    agg_dates = aggregation_dates, \
                                    date_to_agg_date = date_to_agg_date, \
                                    dist_aggregate = BIN_AGGREGATE, \
                                    bin_stops = bin_stops, normalize_to = 100)
  for d in aggregated_buckets:
    aggregated_buckets[d] = normalize_array(aggregated_buckets[d])
    if RESCALE:
      aggregated_buckets[d] = make_distribution_normal(aggregated_buckets[d], \
                                    bins = actual_bin_stops, bin_width = BIN_SIZE, \
                                    val_range = (THRESHOLD, MAX_RATING), scale_bins = 100)

  reversed_stops = list(reversed(actual_bin_stops))
  metrics_bins = {actual_bin_stops[s]: vals \
                  for s, vals in enumerate(zip(*aggregated_buckets.values()))}

  if SHOW_BIN_COUNTS:
    print()
    print("=== BIN COUNTS BY RATING STEP ===")
    for b in metrics_bins:
      s = str(b)
      for v in metrics_bins[b]:
        s += '\t{r:5.2f}'.format(r = v)
      print(s)

  if SHOW_GRAPH:
    graph_metrics = get_graph_metrics(metrics_bins, stops = reversed_stops, \
                                      dates = aggregation_dates, \
                                      cumulatives = GRAPH_CUMULATIVES)

    title_text = 'Percent of ' + ((str(THRESHOLD) + '+ ') if THRESHOLD else '') \
                    + 'Players above Rating ' + (" (Rescaled)" if RESCALE else '')
    ylabel = "Rating"
    xlabel = 'Percent of ' + ((str(THRESHOLD) + '+ ') if THRESHOLD else '') \
                    + 'Players above rating'
    graph_annotations = {'TYPE': typ, 'FORMAT': frmt, \
                          'START_DATE': START_DATE, 'END_DATE': END_DATE, \
                          'AGGREGATION_WINDOW': AGGREGATION_WINDOW, \
                          'AGG_TYPE': BIN_AGGREGATE, 'AGG_LOCATION': 'x', \
                          'TITLE': title_text, 'YLABEL': ylabel, 'XLABEL': xlabel, \
                          'DTYPE': 'int', \
                          }

    if TRIM_GRAPH_TO:
      yparams_min = TRIM_GRAPH_TO
    else:
      yparams_min = THRESHOLD
      if HIDE_THRESHOLD:
        yparams_min += BIN_SIZE
    yparams_max = MAX_RATING
    if TRIM_EMPTY_ROWS:
      for i, s in enumerate(reversed_stops):
        if graph_metrics['lines'][i][1] == 0:
          yparams_max = s
        else:
          break
    graph_yparams = {'min': yparams_min, 'max': yparams_max, 'step': BIN_SIZE}

    out_filename = 'out/images/interval/avgratings/' + str(THRESHOLD) + '_' \
                    + str(MAX_RATING) + '_' + str(BIN_SIZE) + '_' \
                    + ("TRIM" + str(TRIM_GRAPH_TO) + '_' if TRIM_GRAPH_TO else '') \
                    + ("RESC_" if RESCALE else '') \
                    + AGGREGATION_WINDOW + '_' + BIN_AGGREGATE + '_' \
                    + frmt + '_' + typ + '_' \
                    + str(START_DATE.year) + '_' + str(END_DATE.year) + '.png'
    Path(out_filename).parent.mkdir(exist_ok = True, parents = True)


    plot_interval_graph(graph_metrics, stops = reversed_stops, \
                        annotations = graph_annotations, yparams = graph_yparams, \
                        all_xticks = False, save_filename = out_filename)
