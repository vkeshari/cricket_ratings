from common.output import readable_name_and_country

import numpy as np


def get_player_stats(aggregate_ratings, dates_to_show, top_players = 10):
  all_player_stats = {}
  for d in aggregate_ratings:
    if d not in dates_to_show:
      continue
    for p in aggregate_ratings[d]:
      if p not in all_player_stats:
        all_player_stats[p] = []
      all_player_stats[p].append(aggregate_ratings[d][p])

  player_stats = {}
  for p in all_player_stats:
    player_stats[p] = {}
    player_stats[p]['span'] = len(all_player_stats[p])
    player_stats[p]['max'] = max(all_player_stats[p])
    player_stats[p]['avg'] = np.average(all_player_stats[p])
    player_stats[p]['sum'] = sum(all_player_stats[p])

  return player_stats


def show_top_stats(player_stats, sort_by = 'sum', top_players = 10, dtype = 'float'):
  assert not set(sort_by) - {'span', 'avg', 'max', 'sum'}
  assert dtype in {'int', 'float'}

  sort_criteria = lambda item: [item[1][s] for s in sort_by]
  player_stats = dict(sorted(player_stats.items(), \
                                    key = sort_criteria, reverse = True))

  sort_string = ''
  for sb in sort_by:
    sort_string += sb + ', '
  sort_string.rstrip(', ')
  print('\n=== Top ' + str(top_players) + ' Players by ' + sort_string + ' ===')
  print ("RANK\tSPAN\tAVG\tMAX\tSUM\tNAME")
  for i, (p, stats) in enumerate(player_stats.items()):
    if dtype == 'float':
      print (str(i + 1) + ',' + '\t' + '{s:2d}'.format(s = stats['span']) + ',' \
                              + '\t' + '{s:5.2f}'.format(s = stats['avg']) + ',' \
                              + '\t' + '{s:5.2f}'.format(s = stats['max']) + ',' \
                              + '\t' + '{s:5.2f}'.format(s = stats['sum']) + ',' \
                              + '\t' + readable_name_and_country(p))
    elif dtype == 'int':
      print (str(i + 1) + ',' + '\t' + '{s:2d}'.format(s = stats['span']) + ',' \
                              + '\t' + '{s:3.0f}'.format(s = stats['avg']) + ',' \
                              + '\t' + '{s:3d}'.format(s = stats['max']) + ',' \
                              + '\t' + '{s:5d}'.format(s = stats['sum']) + ',' \
                              + '\t' + readable_name_and_country(p))
    if i >= top_players - 1:
      break
