from common.output import pretty_format

from matplotlib import pyplot as plt

import math


def filter_to_yrange(yparams, graph_metrics, stops):
  filtered_stop_indices = []
  for i, s in enumerate(stops):
    if s >= yparams['min'] and s <= yparams['max']:
      filtered_stop_indices.append(i)

  filtered_stops = [s for i, s in enumerate(stops) if i in filtered_stop_indices]
  filtered_graph_metrics = {}
  for metric in graph_metrics:
    filtered_graph_metrics[metric] = [m for i, m in enumerate(graph_metrics[metric]) \
                                        if i in filtered_stop_indices]

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
                            medal_stats = {}, show_medals = False, all_xticks = True, \
                            save_filename = ''):
  assert graph_metrics, "No graph_metrics provided"
  assert not {'lines', 'avgs', 'outers', 'inners'} - graph_metrics.keys(), \
          "Not all graph metrics provided"
  assert stops, "No stops provided"
  assert annotations, "No annotations provided"
  assert not {'TYPE', 'FORMAT', 'START_DATE', 'END_DATE', \
                  'AGGREGATION_WINDOW', 'AGG_TYPE', 'AGG_LOCATION', \
                  'LABEL_METRIC', 'LABEL_KEY', 'LABEL_TEXT', 'DTYPE'} \
              ^ annotations.keys(), \
          "Not all annotations provided"
  assert annotations['AGG_LOCATION'] in {'', 'x', 'y'}
  assert yparams, "No yparams provided"
  assert not {'min', 'max', 'step'} ^ yparams.keys(), "yparams must be min, max and step"
  if show_medals:
    assert medal_stats, "No medal_stats provided"
    assert not {'gold', 'silver', 'bronze'} ^ medal_stats.keys(), \
          "medal_stats keys must be gold, silver and bronze"
    for medal in medal_stats:
      for metric in {'threshold', 'exp_num'}:
        assert medal_stats[medal][metric], "No " + metric + " in medal_stats for " + medal

  graph_metrics, stops = filter_to_yrange(yparams, graph_metrics, stops)

  resolution = tuple([7.2, 7.2])
  fig, ax = plt.subplots(figsize = resolution)

  title_text = annotations['LABEL_METRIC'] + " Above " \
                + annotations['LABEL_TEXT'] + "\n" \
                + pretty_format(annotations['FORMAT'], annotations['TYPE']) \
                + ' (' + str(annotations['START_DATE']) \
                + ' to ' + str(annotations['END_DATE']) + ')'
  ax.set_title(title_text, fontsize ='xx-large')

  agg_text = ''
  if annotations['AGG_LOCATION']:
    agg_text = ' (' + annotations['AGGREGATION_WINDOW'] \
                    + ' ' + annotations['AGG_TYPE'] + ')'

  ylabel = annotations['LABEL_TEXT'] \
                +  (agg_text if annotations['AGG_LOCATION'] == 'y' else '')
  ax.set_ylabel(ylabel, fontsize ='x-large')

  xlabel = annotations['LABEL_METRIC'] + ' above ' + annotations['LABEL_KEY'] \
                + (agg_text if annotations['AGG_LOCATION'] == 'x' else '')
  ax.set_xlabel(xlabel, fontsize ='x-large')

  ymin = yparams['min'] - yparams['step']
  ymax = yparams['max']
  ax.set_ylim(ymin, ymax)
  ax.set_yticks(stops)
  if annotations['DTYPE'] == 'float':
    ax.set_yticklabels(["{s:.2f}".format(s = s) for s in stops], \
                            fontsize ='large')
  else:
    ax.set_yticklabels([str(s) for s in stops], \
                            fontsize ='large')  

  xmax = -1
  for i, s in enumerate(stops):
    line_max = graph_metrics['lines'][i][1]
    if  line_max > xmax:
      xmax = line_max
  ax.set_xlim(0, xmax)

  xtickmajor = 2
  xtickminor = 1
  if xmax > 25:
    xtickmajor = 5
  if xmax > 50:
    xtickmajor = 10
    xtickminor = 2
  xticks_major = list(range(0, math.floor(xmax + 1), xtickmajor))
  xticks_minor = list(range(0, math.floor(xmax + 1), xtickminor))

  ax.set_xticks(xticks_major)
  ax.grid(True, which = 'major', axis = 'x', alpha = 0.8)
  ax.set_xticks(xticks_minor, minor = True)
  ax.grid(True, which = 'minor', axis = 'x', alpha = 0.4)

  xticklabels = [str(x) for x in xticks_major]
  ax.set_xticklabels(xticklabels, fontsize ='large')

  outer_starts = [interval['start'] for interval in graph_metrics['outers']]
  outer_widths = [interval['width'] for interval in graph_metrics['outers']]
  ax.barh(y = stops, width = outer_widths, \
            align = 'center', height = 0.9 * yparams['step'], left = outer_starts, \
            color = 'darkgrey', alpha = 0.4, label = "Middle 80%", \
          )

  inner_starts = [interval['start'] for interval in graph_metrics['inners']]
  inner_widths = [interval['width'] for interval in graph_metrics['inners']]
  ax.barh(y = stops, width = inner_widths, \
          align = 'center', height = 0.8 * yparams['step'], left = inner_starts, \
          color = 'green', alpha = 0.5, label = "Middle 50%", \
        )

  plt.plot(graph_metrics['avgs'], stops, \
                    linewidth = 0, alpha = 0.5, \
                    marker = 'x', markeredgecolor = 'blue', \
                    markersize = 8, markeredgewidth = 2, label = "Average")

  for i, s in enumerate(stops):
    plt.plot(list(graph_metrics['lines'][i]), [s, s], linewidth = 2, \
                      color = 'black', alpha = 0.9, \
                      marker = 'o', markerfacecolor = 'red', \
                      markersize = 3, markeredgewidth = 0, label = "Full Range" if i == 0 else '')

  if show_medals:
    for medal in medal_stats:
      if ymin < medal_stats[medal]['threshold']:
        plot_medal_indicators(medal, \
                              medal_threshold = medal_stats[medal]['threshold'], \
                              exp_num = medal_stats[medal]['exp_num'], \
                              ylims = {'ymin': ymin, 'ymax': ymax}, \
                              xlims = {'xmax': xmax}
                              )

  ax.legend(loc = 'best', fontsize = 'large')
  fig.tight_layout()

  if not save_filename:
    plt.show()
  else:
    fig.savefig(save_filename)
    print("Written: " + save_filename)
