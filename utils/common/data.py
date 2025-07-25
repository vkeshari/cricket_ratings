from common.aggregation import is_aggregation_window_start
from common.output import string_to_date

from os import listdir
from pathlib import Path

import math
import pickle

SUFFIX = ''
REBUILD_DATA = False

def get_days_with_change(daily_data, agg_window, consider_player_keys = False):
  assert agg_window in ['', 'monthly', 'quarterly', 'halfyearly', \
                          'yearly', 'fiveyearly', 'decadal'], \
        "Invalid agg_window provided"

  changed_days = set()
  last_daily_data = {}
  for d in daily_data:
    changed = False
    if not last_daily_data:
      changed = True
    elif consider_player_keys and daily_data[d].keys() ^ last_daily_data.keys():
      changed = True
    else:
      for p in daily_data[d]:
        if p in last_daily_data and not daily_data[d][p] == last_daily_data[p]:
          changed = True
          break
    if changed or agg_window and is_aggregation_window_start(d, agg_window):
      changed_days.add(d)
    last_daily_data = daily_data[d]

  return changed_days


def get_daily_ratings(typ, frmt, changed_days_criteria = '', agg_window = '', \
                          allrounders_geom_mean = False, rebuild_data = False, suffix = ''):
  assert typ in ['batting', 'bowling', 'allrounder'], "Invalid type provided"
  assert frmt in ['test', 'odi', 't20'], "Invalid format provided"
  assert changed_days_criteria in ['', 'rating', 'rank', 'either', 'both'], \
        "Invalid changed_days_criteria"
  assert agg_window in ['', 'monthly', 'quarterly', 'halfyearly', \
                          'yearly', 'fiveyearly', 'decadal'], \
        "Invalid agg_window provided"
  
  if not suffix:
    suffix = SUFFIX

  pickle_filename = typ + '_' + frmt + '_' + changed_days_criteria + '_' + agg_window + '_' \
                    + str(allrounders_geom_mean)
  pickle_file = Path('pickle' + suffix + '/' + pickle_filename)

  rebuild_data = rebuild_data or REBUILD_DATA
  if not rebuild_data and pickle_file.exists():
    with open(pickle_file, 'rb') as f:
      (daily_ratings, daily_ranks) = pickle.load(f)
      print("UNPICKLED!")

      print("Daily ratings data read for " + str(len(daily_ratings)) + " days" )
      print("Daily ranks data read for " + str(len(daily_ranks)) + " days" )
  
  else:
    daily_ratings = {}
    daily_ranks = {}
    dates_parsed = set()

    player_dir = 'players' + suffix + '/' + typ + '/' + frmt
    player_files = listdir(player_dir)
    for p in player_files:
      lines = []
      with open(player_dir + '/' + p, 'r') as f:
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
          rating = int(math.pow(rating, 2) / 1000)
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
        rank_change_days = get_days_with_change(daily_ranks, agg_window, \
                                                consider_player_keys = True)

      change_days = set()
      if changed_days_criteria == 'rating':
        change_days = rating_change_days
      elif changed_days_criteria == 'rank':
        change_days = rank_change_days
      elif changed_days_criteria == 'either':
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
    
    pickle_file.parent.mkdir(exist_ok = True, parents = True)
    with open(pickle_file, 'wb+') as f:
      pickle.dump([daily_ratings, daily_ranks], f)
      print("PICKLED!")

  return daily_ratings, daily_ranks

