from common.aggregation import get_aggregation_dates, date_to_aggregation_date, \
                                get_aggregate_ratings, get_metrics_by_stops, \
                                get_aggregation_window_width, VALID_AGGREGATIONS
from common.data import get_daily_ratings
from common.interval_metrics import get_graph_metrics, get_medal_stats
from common.output import pretty_format, get_timescale_xticks, resolution_by_span
from common.stats import VALID_STATS

from datetime import date, timedelta
from matplotlib import pyplot as plt
from pathlib import Path

ONE_DAY = timedelta(days = 1)

# ['batting', 'bowling', 'allrounder']
TYPE = 'batting'
# ['test', 'odi', 't20']
FORMAT = 't20'

# Graph date range
START_DATE = date(2009, 1, 1)
END_DATE = date(2024, 1, 1)

# Upper and lower bounds of ratings to show
THRESHOLD = 500
MAX_RATING = 1000
RATING_STEP = 10

# ['', 'rating', 'rank', 'either', 'both']
CHANGED_DAYS_CRITERIA = 'rating'

# Aggregation
# See common.aggregation.VALID_AGGREGATIONS for possible windows
AGGREGATION_WINDOW = 'yearly'
# See common.stats.VALID_STATS for possible aggregate stats
PLAYER_AGGREGATE = 'max'

SHOW_GRAPH = True
TOP_PLAYERS = 10
SHOW_ALL_RANKS = True

SHOW_MEDALS = True
AVG_MEDAL_CUMULATIVE_COUNTS = [2, 5, 10]
MEDAL_LABELS = ['gold', 'silver', 'bronze']

# Alternate way to calculate allrounder ratings. Use geometric mean of batting and bowling.
ALLROUNDERS_GEOM_MEAN = True

assert TYPE in ['batting', 'bowling', 'allrounder'], "Invalid TYPE provided"
assert FORMAT in ['test', 'odi', 't20'], "Invalid FORMAT provided"
assert START_DATE < END_DATE, "START_DATE must be earlier than END_DATE"
assert END_DATE <= date.today(), "Future END_DATE requested"

assert MAX_RATING <= 1000, "MAX_RATING must not be greater than 1000"
assert THRESHOLD >= 0 and THRESHOLD < MAX_RATING, \
      "THRESHOLD must be between 0 and MAX_RATING"
assert RATING_STEP >= 5, "RATING_STEP must be at least 5"

assert CHANGED_DAYS_CRITERIA in ['', 'rating', 'rank', 'either', 'both']

assert AGGREGATION_WINDOW in VALID_AGGREGATIONS, "Invalid AGGREGATION_WINDOW provided"
assert PLAYER_AGGREGATE in VALID_STATS, "Invalid PLAYER_AGGREGATE provided"

assert TOP_PLAYERS > 5, "TOP_PLAYERS must be at least 5"

for amcc in AVG_MEDAL_CUMULATIVE_COUNTS:
  assert amcc > 0, "All values in AVG_MEDAL_CUMULATIVE_COUNTS must be positive"
assert AVG_MEDAL_CUMULATIVE_COUNTS == sorted(AVG_MEDAL_CUMULATIVE_COUNTS), \
        "AVG_MEDAL_CUMULATIVE_COUNTS must be sorted"
if MEDAL_LABELS:
  assert len(MEDAL_LABELS) == len(AVG_MEDAL_CUMULATIVE_COUNTS), \
        "MEDAL_LABELS and AVG_MEDAL_CUMULATIVE_COUNTS should have the same length"


if FORMAT == 'test':
  SKIP_YEARS = list(range(1913, 1921)) + list(range(1940, 1946)) + [1970]
elif FORMAT == 'odi':
  SKIP_YEARS = [2018]
elif FORMAT == 't20':
  SKIP_YEARS = [2011]

MEDAL_COUNT = len(AVG_MEDAL_CUMULATIVE_COUNTS)
if MEDAL_LABELS:
  ALL_MEDALS = MEDAL_LABELS
else:
  ALL_MEDALS = ['T' + str(c) for c in AVG_MEDAL_CUMULATIVE_COUNTS]

print (FORMAT + '\t' + TYPE)
print (str(START_DATE) + ' to ' + str(END_DATE))
print (str(THRESHOLD) + ' : ' + str(MAX_RATING))
print (AGGREGATION_WINDOW + ' / ' + PLAYER_AGGREGATE)

daily_ratings, _ = get_daily_ratings(TYPE, FORMAT, \
                          changed_days_criteria = CHANGED_DAYS_CRITERIA, \
                          agg_window = AGGREGATION_WINDOW, \
                          allrounders_geom_mean = ALLROUNDERS_GEOM_MEAN)

dates_to_show = get_aggregation_dates(daily_ratings, agg_window = AGGREGATION_WINDOW, \
                                      start_date = START_DATE, end_date = END_DATE)
date_to_agg_date = date_to_aggregation_date(dates = list(daily_ratings.keys()), \
                                                    aggregation_dates = dates_to_show)

aggregate_ratings = get_aggregate_ratings(daily_ratings, agg_dates = dates_to_show, \
                                          date_to_agg_date = date_to_agg_date, \
                                          player_aggregate = PLAYER_AGGREGATE)

for i, d in enumerate(dates_to_show):
  if d.year in SKIP_YEARS:
    del dates_to_show[i]
if dates_to_show[-1] == END_DATE:
  dates_to_show.pop()


def filter_by_threshold(aggregate_ratings):
  aggregate_filtered = {}
  for d in aggregate_ratings:
    aggregate_filtered[d] = {}
    for p in aggregate_ratings[d]:
      rating = aggregate_ratings[d][p]
      if rating >= THRESHOLD:
        aggregate_filtered[d][p] = rating
  return aggregate_filtered

aggregate_ratings = filter_by_threshold(aggregate_ratings)

if SHOW_GRAPH:
  graph_dates = [d for d in aggregate_ratings.keys() if d.year not in SKIP_YEARS]
  agg_window_width = get_aggregation_window_width(AGGREGATION_WINDOW)
  half_agg_window = timedelta(days = int((agg_window_width / 2).days))
  date_plot_locs = [d + half_agg_window for d in graph_dates]

  ranks_to_ratings = {rank: {} for rank in range(100)}
  for d in graph_dates:
    sorted_ratings = sorted(aggregate_ratings[d].values(), reverse = True)
    for rank in ranks_to_ratings:
      if rank < len(sorted_ratings):
        ranks_to_ratings[rank][d] = sorted_ratings[rank]
      else:
        ranks_to_ratings[rank][d] = THRESHOLD - 100

  if SHOW_MEDALS:
    rating_stops = list(range(THRESHOLD, MAX_RATING, RATING_STEP))
    actual_rating_stops = rating_stops[ : -1]

    metrics_bins, player_counts_by_step, player_periods = \
            get_metrics_by_stops(aggregate_ratings, stops = rating_stops, \
                                  dates = dates_to_show)

    reversed_stops = list(reversed(actual_rating_stops))

    graph_metrics = get_graph_metrics(metrics_bins, stops = reversed_stops, \
                                      dates = dates_to_show, cumulatives = True)


    medal_stats = get_medal_stats(graph_metrics, stops = reversed_stops, \
                                  all_medals = ALL_MEDALS, \
                                  avg_medal_cumulative_counts = AVG_MEDAL_CUMULATIVE_COUNTS)


  resolution, aspect_ratio = resolution_by_span(START_DATE, END_DATE, \
                                                prefer_wide = True)
  fig, ax = plt.subplots(figsize = resolution)

  agg_text = '(' + AGGREGATION_WINDOW + ' ' + PLAYER_AGGREGATE + ')'

  title_text = "Ratings of Top " + str(TOP_PLAYERS) + " Players " \
                + agg_text + "\n" + pretty_format(FORMAT, TYPE) \
                + ' (' + str(START_DATE) + ' to ' + str(END_DATE) + ')'
  ax.set_title(title_text, fontsize ='x-large')

  ylabel = "Rating " + agg_text
  ax.set_ylabel(ylabel, fontsize ='x-large')

  xlabel = "Date"
  ax.set_xlabel(xlabel, fontsize ='x-large')

  ymin = THRESHOLD
  ymax = MAX_RATING
  ax.set_ylim(ymin, ymax)

  yticks_major = range(THRESHOLD, MAX_RATING + 1, RATING_STEP * 5)
  yticks_minor = range(THRESHOLD, MAX_RATING + 1, RATING_STEP)
  ax.set_yticks(yticks_major)
  ax.set_yticks(yticks_minor, minor = True)
  ax.set_yticklabels([str(y) for y in yticks_major], fontsize ='large')

  xticks_major, xticks_minor, xticklabels = \
          get_timescale_xticks(START_DATE, END_DATE, format = aspect_ratio)

  xmin, xmax = date(START_DATE.year, 1, 1), date(END_DATE.year, 1, 1)
  ax.set_xlim(xmin, xmax)

  ax.set_xticks(xticks_major)
  ax.set_xticks(xticks_minor, minor = True)
  ax.set_xticklabels(xticklabels, fontsize ='large')

  ax.grid(True, which = 'major', axis = 'both', alpha = 0.8)
  ax.grid(True, which = 'minor', axis = 'both', alpha = 0.4)

  for rank in ranks_to_ratings:
    if rank < TOP_PLAYERS:
      ax.plot(date_plot_locs, ranks_to_ratings[rank].values(), \
                linewidth = 0, marker = 'o', markersize = 10, alpha = 0.5, \
                label = "Rank " + str(rank + 1))
    elif SHOW_ALL_RANKS:
      ax.plot(date_plot_locs, ranks_to_ratings[rank].values(), \
                linewidth = 0, marker = 'o', markersize = 10, alpha = 0.2, \
                color = 'darkgrey')


  if SHOW_MEDALS:
    for medal in medal_stats:
      medal_threshold = medal_stats[medal]['threshold']
      plt.axhline(y = medal_threshold, linestyle = '--', linewidth = 1, \
                color = 'red', alpha = 0.7)
      plt.text(x = xmax, y = medal_threshold, color = 'red', \
                s = medal.upper(), alpha = 0.8, fontsize = 'large', \
                horizontalalignment = 'left', verticalalignment = 'center')

  fig.tight_layout()

  out_filename = 'out/images/line/topplayers/ratings/' \
                  + str(THRESHOLD) + '_' + str(MAX_RATING) + '_' \
                  + str(RATING_STEP) + '_' \
                  + ('ALL_' if SHOW_ALL_RANKS else '') \
                  + (str(MEDAL_COUNT) + 'MEDALS_' if SHOW_MEDALS and MEDAL_COUNT else '') \
                  + AGGREGATION_WINDOW + '_' + PLAYER_AGGREGATE + '_' \
                  + FORMAT + '_' + TYPE \
                  + ('GEOM' if TYPE == 'allrounder' and ALLROUNDERS_GEOM_MEAN else '') \
                  + '_' + str(START_DATE.year) + '_' + str(END_DATE.year) + '.png'

  if not out_filename:
    plt.show()
  else:
    Path(out_filename).parent.mkdir(exist_ok = True, parents = True)
    fig.savefig(out_filename)
    print("Written: " + out_filename)
