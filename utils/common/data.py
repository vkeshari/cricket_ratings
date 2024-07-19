from common.aggregation import is_aggregation_window_start
from common.output import string_to_date

from os import listdir


def get_days_with_change(daily_data, agg_window):
  assert agg_window in ['', 'monthly', 'quarterly', 'halfyearly', \
                          'yearly', 'fiveyearly', 'decadal'], \
        "Invalid agg_window provided"

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
    if changed or agg_window and is_aggregation_window_start(d, agg_window):
      changed_days.add(d)
    last_daily_data = daily_data[d]

  return changed_days


def get_daily_ratings(typ, frmt, changed_days_criteria = '', agg_window = '', \
                                  allrounders_geom_mean = False):
  assert typ in ['batting', 'bowling', 'allrounder'], "Invalid type provided"
  assert frmt in ['test', 'odi', 't20'], "Invalid format provided"
  assert changed_days_criteria in ['', 'rating', 'rank', 'either', 'both'], \
        "Invalid changed_days_criteria"
  assert agg_window in ['', 'monthly', 'quarterly', 'halfyearly', \
                          'yearly', 'fiveyearly', 'decadal'], \
        "Invalid agg_window provided"

  daily_ratings = {}
  daily_ranks = {}
  dates_parsed = set()

  player_files = listdir('players/' + typ + '/' + frmt)
  for p in player_files:
    lines = []
    with open('players/' + typ + '/' + frmt + '/' + p, 'r') as f:
      lines += f.readlines()

    for l in lines:
      parts = l.split(',')
      d = string_to_date(parts[0])
      if d not in dates_parsed:
        daily_ratings[d] = {}
        daily_ranks[d] = {}
        dates_parsed.add(d)

      rating = eval(parts[2])
      if typ == 'allrounder' and not allrounders_geom_mean:
        rating = int((rating ^ 2) / 1000)
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

  if changed_days_criteria:
    rating_change_days = set()
    rank_change_days = set()
    if changed_days_criteria in {'rating', 'either', 'both'}:
      rating_change_days = get_days_with_change(daily_ratings, agg_window)
    if changed_days_criteria in {'rank', 'either', 'both'}:
      rank_change_days = get_days_with_change(daily_ranks, agg_window)

    change_days = set()
    if changed_days_criteria in {'rating', 'rank', 'either'}:
      change_days = rating_change_days | rank_change_days
    elif changed_days_criteria == 'both':
      change_days = rating_change_days & rank_change_days

    daily_ratings = dict(filter(lambda item: item[0] in change_days, \
                              daily_ratings.items()))
    daily_ranks = dict(filter(lambda item: item[0] in change_days, \
                            daily_ranks.items()))

  print("Daily ratings data built for " + str(len(daily_ratings)) + " days" )
  print("Daily ranks data built for " + str(len(daily_ranks)) + " days" )
  assert not daily_ratings.keys() ^ daily_ranks.keys(), \
          "Key mismatch between daily_ratings and daily_ranks"

  return daily_ratings, daily_ranks

