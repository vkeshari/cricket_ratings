from common.output import readable_name_and_country
from common.stats import get_stats_for_list

import numpy as np


def get_graph_stats(data):
  outer_interval = {}
  outer_interval['start'] = get_stats_for_list(data, stat_type = 'p10')
  outer_interval['end'] = get_stats_for_list(data, stat_type = 'p90')
  outer_interval['width'] = outer_interval['end'] - outer_interval['start']
  inner_interval = {}
  inner_interval['start'] = get_stats_for_list(data, stat_type = 'p25')
  inner_interval['end'] = get_stats_for_list(data, stat_type = 'p75')
  inner_interval['width'] = inner_interval['end'] - inner_interval['start']
  
  line = (min(data), max(data))
  avg = get_stats_for_list(data, stat_type = 'avg')

  return outer_interval, inner_interval, line, avg


def get_graph_metrics(metrics_bins, stops, dates, cumulatives):

  graph_metrics = {'outers': [], 'inners': [], 'lines': [], 'avgs': []}

  cum_metrics_bins = {}
  for s in stops:
    cum_metrics_bins[s] = [0] * len(dates)

  last_s = -1
  for s in stops:
    for i, v in enumerate(metrics_bins[s]):
      if last_s == -1:
        cum_metrics_bins[s][i] = 0
      else:
        cum_metrics_bins[s][i] = cum_metrics_bins[last_s][i]
      cum_metrics_bins[s][i] += v
    last_s = s

    if cumulatives:
      (outer, inner, line, avg) = get_graph_stats(cum_metrics_bins[s])
    else:
      (outer, inner, line, avg) = get_graph_stats(metrics_bins[s])

    graph_metrics['outers'].append(outer)
    graph_metrics['inners'].append(inner)
    graph_metrics['lines'].append(line)
    graph_metrics['avgs'].append(avg)

  return graph_metrics


def get_medal_stats(graph_metrics, stops, all_medals, avg_medal_cumulative_counts):
  medal_stats = {medal: {} for medal in all_medals}

  medal_indices = {medal: -1 for medal in all_medals}
  for i, av in enumerate(graph_metrics['avgs']):
    for j, medal in enumerate(medal_indices.keys()):
      if medal_indices[medal] == -1:
        medal_desired =  avg_medal_cumulative_counts[j]
        if av > medal_desired:
          prev_av = graph_metrics['avgs'][i - 1]
          if av - medal_desired > medal_desired - prev_av:
            medal_indices[medal] = i - 1
          else:
            medal_indices[medal] = i

  for medal in all_medals:
    medal_stats[medal]['threshold'] = \
                      list(stops)[medal_indices[medal]]

  for medal in all_medals:
    medal_stats[medal]['exp_num'] = graph_metrics['avgs'][medal_indices[medal]]

  print("\n=== Medal Thresholds ===")
  for medal in all_medals:
    print (medal + ':\t{m:.2f}'.format(m = medal_stats[medal]['threshold']))

  return medal_stats


def get_heirarchical_sort_lambda_key(medals):
  key = '('
  for m in medals:
    key += "item[1][" + repr(m) + "],"
  key += ')'
  return key


def get_player_medals(player_counts_by_step, medal_stats, all_medals):
  player_medals = {}

  for p in player_counts_by_step:
    if p not in player_medals:
      player_medals[p] = {medal: 0 for medal in all_medals}
    for r in sorted(player_counts_by_step[p].keys()):
      reversed_medals = list(reversed(all_medals))
      bottom_medal = reversed_medals[0]
      if r < medal_stats[bottom_medal]['threshold']:
        continue
      for i, m in enumerate(reversed_medals):
        if i == 0:
          continue
        prev_medal = reversed_medals[i - 1]
        if r < medal_stats[m]['threshold']:
          player_medals[p][prev_medal] += player_counts_by_step[p][r]
          break
      else:
        top_medal = all_medals[0]
        player_medals[p][top_medal] += player_counts_by_step[p][r]

  sort_key = get_heirarchical_sort_lambda_key(all_medals)
  player_medals = dict(sorted(player_medals.items(),
                                key = lambda item: eval(sort_key), \
                                reverse = True))

  return player_medals


def show_top_medals(player_medals, player_periods, all_medals, \
                      top_players = 10, by_percentage = False):
  medal_str = ''
  for m in all_medals:
    medal_str += '\t' + m.upper() + ','

  print('\n=== Top ' + str(top_players) + ' Players by Medals ===')
  print('RANK\tSPAN,\tMEDALS,' + medal_str + '\tPLAYER NAME')

  for i, p in enumerate(player_medals.keys()):
    s = str(i + 1) + ',\t' + str(player_periods[p]) + ','
    total_medals = sum(player_medals[p].values())
    if by_percentage:
      s += '\t{v:.2f}'.format(v = total_medals) + ','
    else:
      s += '\t' + str(total_medals) + ','
    for medal in all_medals:
      if by_percentage:
        s += '\t{v:.2f}'.format(v = player_medals[p][medal]) + ','
      else:
        s += '\t' + str(player_medals[p][medal]) + ','
    s += '\t' + readable_name_and_country(p)
    print (s)

    if i >= top_players - 1:
      break
