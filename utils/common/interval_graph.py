from matplotlib import pyplot as plt


def filter_to_ymin(ymin, graph_metrics, stops):
  filtered_stops = []
  for s in stops:
    if s >= ymin:
      filtered_stops.append(s)

  filtered_graph_metrics = {}
  for metric in graph_metrics:
    filtered_graph_metrics[metric] = graph_metrics[metric][ : len(filtered_stops)]

  return filtered_graph_metrics, filtered_stops


def plot_medal_indicators(medal, medal_threshold, exp_num, ylims, xlims):
  medal_label = '{v:.2f}'.format(v = exp_num)
  plt.axhline(y = medal_threshold, linestyle = '--', linewidth = 1, \
                color = 'black', alpha = 0.8)
  plt.text(x = xlims['xmax'] - 1, y = medal_threshold, \
                s = medal.upper(), alpha = 0.8, fontsize = 'large', \
                horizontalalignment = 'right', verticalalignment = 'bottom')
  medal_line_ymax = (medal_threshold - ylims['ymin']) / (ylims['ymax'] - ylims['ymin'])
  plt.axvline(x = exp_num, linestyle = ':', linewidth = 1, \
                color = 'black', alpha = 0.8, ymax = medal_line_ymax)


def plot_interval_graph(graph_metrics, stops, annotations, yparams, \
                            medal_stats, show_medals = False):
  assert graph_metrics, "No graph_metrics provided"
  assert not {'lines', 'avgs', 'outers', 'inners'} - graph_metrics.keys(), \
          "Not all graph metrics provided"
  assert stops, "No stops provided"
  assert annotations, "No annotations provided"
  assert not {'TYPE', 'FORMAT', 'START_DATE', 'END_DATE', \
                  'AGGREGATION_WINDOW', 'PLAYER_AGGREGATE', \
                  'LABEL_KEY', 'LABEL_TEXT', 'DTYPE'} \
              - annotations.keys(), \
          "Not all annotations provided"
  assert yparams, "No yparams provided"
  assert not {'min', 'max', 'step'} - yparams.keys(), "Not all yparams provided"
  if show_medals:
    assert medal_stats, "No medal_stats provided"
    assert not {'gold', 'silver', 'bronze'} - medal_stats.keys(), \
          "medal_stats keys are not gold, silver and bronze"
    for medal in medal_stats:
      for metric in {'threshold', 'exp_num'}:
        assert medal_stats[medal][metric], "No " + metric + " in medal_stats for " + medal

  graph_metrics, stops = filter_to_ymin(yparams['min'], graph_metrics, stops)

  resolution = tuple([7.2, 7.2])
  fig, ax = plt.subplots(figsize = resolution)

  title_text = "No. of players above " + annotations['LABEL_TEXT'] + "\n" \
                + annotations['FORMAT'] + ' ' + annotations['TYPE'] \
                + ' (' + str(annotations['START_DATE']) \
                + ' to ' + str(annotations['END_DATE']) + ')'
  ax.set_title(title_text, fontsize ='xx-large')

  ylabel = annotations['LABEL_TEXT'] \
                + ' (' + annotations['AGGREGATION_WINDOW'] \
                + ' ' + annotations['PLAYER_AGGREGATE'] + ')'
  ax.set_ylabel(ylabel, fontsize ='x-large')
  ax.set_xlabel('No. of players above ' + annotations['LABEL_KEY'], fontsize ='x-large')

  ymin = yparams['min'] - yparams['step']
  ymax = yparams['max']
  ax.set_ylim(ymin, ymax)
  ax.set_yticks(stops)
  if annotations['DTYPE'] == 'float':
    ax.set_yticklabels(["{s:.2f}".format(s = s) for s in stops], \
                            fontsize ='medium')
  else:
    ax.set_yticklabels([str(s) for s in stops], \
                            fontsize ='medium')  

  xmax = -1
  for i, s in enumerate(stops):
    line_max = graph_metrics['lines'][i][1]
    if  line_max > xmax:
      xmax = line_max
  xmax += 1

  ax.set_xlim(0, xmax)
  xticks = list(range(0, xmax + 1, 1))
  ax.set_xticks(xticks)

  xlabwidth = 1
  if xmax > 25:
    xlabwidth = 2
  if xmax > 50:
    xlabwidth = 5
  if xmax > 100:
    xlabwidth = 10
  xticklabels = [str(x) if x % xlabwidth == 0 else '' for x in xticks]
  ax.set_xticklabels(xticklabels, fontsize ='medium')

  ax.grid(True, which = 'both', axis = 'x', alpha = 0.5)

  outer_starts = [interval['start'] for interval in graph_metrics['outers']]
  outer_widths = [interval['width'] for interval in graph_metrics['outers']]
  ax.barh(y = stops, width = outer_widths, \
            align = 'center', height = 0.9 * yparams['step'], left = outer_starts, \
            color = 'darkgrey', alpha = 0.4, \
          )

  inner_starts = [interval['start'] for interval in graph_metrics['inners']]
  inner_widths = [interval['width'] for interval in graph_metrics['inners']]
  ax.barh(y = stops, width = inner_widths, \
          align = 'center', height = 0.8 * yparams['step'], left = inner_starts, \
          color = 'green', alpha = 0.5, \
        )

  plt.plot(graph_metrics['avgs'], stops, \
                    linewidth = 0, alpha = 0.5, \
                    marker = 'x', markeredgecolor = 'blue', \
                    markersize = 8, markeredgewidth = 2)

  for i, s in enumerate(stops):
    plt.plot(list(graph_metrics['lines'][i]), [s, s], linewidth = 2, \
                      color = 'black', alpha = 0.9, \
                      marker = 'o', markerfacecolor = 'red', \
                      markersize = 3, markeredgewidth = 0)

  if show_medals:
    for medal in medal_stats:
      plot_medal_indicators(medal, \
                            medal_threshold = medal_stats[medal]['threshold'], \
                            exp_num = medal_stats[medal]['exp_num'], \
                            ylims = {'ymin': ymin, 'ymax': ymax}, \
                            xlims = {'xmax': xmax}
                            )

  fig.tight_layout()
  plt.show()
