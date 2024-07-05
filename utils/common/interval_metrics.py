from common.output import readable_name_and_country

import numpy as np


def get_graph_stats(data):
  outer_interval = {}
  outer_interval['start'] = np.percentile(data, 10, method = 'nearest')
  outer_interval['end'] = np.percentile(data, 90, method = 'nearest')
  outer_interval['width'] = outer_interval['end'] - outer_interval['start']
  inner_interval = {}
  inner_interval['start'] = np.percentile(data, 25, method = 'nearest')
  inner_interval['end'] = np.percentile(data, 75, method = 'nearest')
  inner_interval['width'] = inner_interval['end'] - inner_interval['start']
  line = (min(data), max(data))
  avg = np.average(data)

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


def get_medal_stats(graph_metrics, stops, avg_medal_cumulative_counts):

  all_medals = avg_medal_cumulative_counts.keys()
  medal_stats = {medal: {} for medal in all_medals}

  medal_indices = {medal: -1 for medal in all_medals}
  for i, av in enumerate(graph_metrics['avgs']):
    for medal in medal_indices:
      if medal_indices[medal] == -1:
        medal_desired =  avg_medal_cumulative_counts[medal]
        if av > medal_desired:
          if av - medal_desired > medal_desired - graph_metrics['avgs'][i - 1]:
            medal_indices[medal] = i - 1
          else:
            medal_indices[medal] = i

  for medal in all_medals:
    medal_stats[medal]['threshold'] = \
                      list(stops)[medal_indices[medal]]

  for medal in all_medals:
    medal_stats[medal]['exp_num'] = graph_metrics['avgs'][medal_indices[medal]]

  print()
  for medal in all_medals:
    print (medal + ':\t{m:.2f}'.format(m = medal_stats[medal]['threshold']))

  return medal_stats


def get_player_medals(player_counts_by_step, medal_stats):

  all_medals = medal_stats.keys()
  player_medals = {}

  for p in player_counts_by_step:
    if p not in player_medals:
      player_medals[p] = {medal: 0 for medal in all_medals}
    for r in sorted(player_counts_by_step[p].keys()):
      if r < medal_stats['bronze']['threshold']:
        continue
      elif r < medal_stats['silver']['threshold']:
        player_medals[p]['bronze'] += player_counts_by_step[p][r]
      elif r < medal_stats['gold']['threshold']:
        player_medals[p]['silver'] += player_counts_by_step[p][r]
      else:
        player_medals[p]['gold'] += player_counts_by_step[p][r]

  player_medals = dict(sorted(player_medals.items(),
                                key = lambda item: (item[1]['gold'], \
                                                    item[1]['silver'],
                                                    item[1]['bronze']), \
                                reverse = True))

  return player_medals


def show_top_players(player_medals, player_periods, top_players, by_percentage = False):
  print('\n=== Top ' + str(top_players) + ' Players ===')
  print('SPAN,\tMEDALS,\tGOLD,\tSILVER,\tBRONZE,\tPLAYER NAME')

  for i, p in enumerate(player_medals):
    s = str(player_periods[p]) + ','
    total_medals = sum(player_medals[p].values())
    if by_percentage:
      s += '\t{v:.2f}'.format(v = total_medals) + ','
    else:
      s += '\t' + str(total_medals) + ','
    for medal in ['gold', 'silver', 'bronze']:
      if by_percentage:
        s += '\t{v:.2f}'.format(v = player_medals[p][medal]) + ','
      else:
        s += '\t' + str(player_medals[p][medal]) + ','
    s += '\t' + readable_name_and_country(p)
    print (s)

    if i >= top_players:
      break
