from common.output import pretty_format, resolution_by_span, \
                          get_timescale_xticks

from datetime import date
from matplotlib import pyplot as plt
from pathlib import Path

import numpy as np
import math


def plot_dist_heatmap(graph_dates, all_bin_counts, all_percentiles, \
                        frmt, typ, agg_window, agg_type, agg_title, \
                        threshold, max_rating, bin_size, \
                        plot_percentiles = False, \
                        log_scale = False, rescale = False, \
                        allrounders_geom_mean = True):

  assert agg_window == 'yearly', "Only yearly windows supported"

  adjusted_start_date = graph_dates[0]
  adjusted_end_date = date(graph_dates[-1].year + 1, 1 ,1)
  date_diff = (graph_dates[1] - graph_dates[0])

  resolution, aspect_ratio = resolution_by_span(adjusted_start_date, adjusted_end_date, \
                                                prefer_wide = True)
  fig, ax = plt.subplots(figsize = resolution)

  title_text = "Heatmap of " + agg_title + " Distribution of Ratings" \
                + (" (Rescaled)" if rescale else '') \
                + "\n" + pretty_format(frmt, typ) \
                + ("(GM)" if typ == 'allrounder' and allrounders_geom_mean else '') \
                + ": " + str(adjusted_start_date) + " to " + str(adjusted_end_date) \
                + ' (' + agg_window + ' ' + agg_type + ')'
  ax.set_title(title_text, fontsize ='x-large')

  ax.set_ylabel('No. of players (normalized to 100)', fontsize ='x-large')

  ax.set_ylabel('Rating', fontsize ='x-large')
  ax.set_ylim(threshold, max_rating)
  possible_yticks_major = range(0, 1000, 100)
  possible_yticks_minor = range(0, 1000, 20)
  yticks_major = [r for r in possible_yticks_major if r >= threshold and r <= max_rating]
  yticks_minor= [r for r in possible_yticks_minor if r >= threshold and r <= max_rating]
  ax.set_yticks(yticks_major)
  ax.set_yticks(yticks_minor, minor = True)
  ax.set_yticklabels([str(y) for y in yticks_major], fontsize ='large')

  ax.set_xlabel('Date', fontsize ='x-large')

  xticks_major, xticks_minor, xticklabels = \
          get_timescale_xticks(adjusted_start_date, adjusted_end_date, \
                                format = aspect_ratio)
  ax.set_xticks(xticks_major)
  ax.set_xticks(xticks_minor, minor = True)
  ax.set_xticklabels(xticklabels, fontsize ='large')

  ax.grid(True, which = 'major', axis = 'both', alpha = 0.6)
  ax.grid(True, which = 'minor', axis = 'both', alpha = 0.3)

  heatmap_changes = np.array(list(zip(*all_bin_counts.values())))
  if log_scale:
    for i, hc in enumerate(heatmap_changes):
      log_vals = [np.log10(v) if v > 0 else -1.5 for v in hc]
      heatmap_changes[i] = log_vals

  plt.imshow(heatmap_changes, origin = 'lower', aspect = 'auto', \
                extent = (adjusted_start_date, adjusted_end_date, \
                            threshold, max_rating))

  ymax = max([max(hc) for hc in heatmap_changes])

  if log_scale:
    cbar_ticks = list(np.linspace(-ymax, ymax, 11))
    cbar_ticklabels = ['{l:.1f}'.format(l = math.pow(10, t)) for t in cbar_ticks]
  else:
    cbar_ticks = list(np.linspace(0, ymax, 6))
    cbar_ticklabels = ['{l:.1f}'.format(l = t) for t in cbar_ticks]
  cbar = plt.colorbar(ticks = cbar_ticks, aspect = 25)
  cbar.ax.set_yticklabels(cbar_ticklabels, fontsize = 'medium')
  if log_scale:
    cbar.set_label(label = 'Interval Frequency (log scale)', size = 'x-large')
  else:
    cbar.set_label(label = 'Interval Frequency', size = 'x-large')
  cbar.ax.tick_params(labelsize = 'medium')

  if plot_percentiles:
    xs = [x + date_diff / 2 for x in all_percentiles.keys()]
    p_to_vals = {}
    for d in all_percentiles:
      for p in all_percentiles[d]:
        if p not in p_to_vals:
          p_to_vals[p] = []
        p_to_vals[p].append(all_percentiles[d][p])

    for p in p_to_vals:
      plt.plot(xs, p_to_vals[p],
              linestyle = '-', linewidth = 5, antialiased = True, \
              alpha = 0.4, color = 'red')
      plt.text(adjusted_end_date, p_to_vals[p][-1], s = "p" + str(p), \
                color = 'red', alpha = 0.8, fontsize = 'medium', \
                horizontalalignment = 'left', verticalalignment = 'center')

  fig.tight_layout()

  out_filename = 'out/images/heatmap/distagg/' + str(threshold) + '_' \
                  + str(max_rating) + '_' + str(bin_size) + '_' \
                  + ('RESC_' if rescale else '') \
                  + ('LOG_' if log_scale else '') \
                  + ('PCT_' if plot_percentiles else '') \
                  + agg_window + '_' + agg_type + '_' \
                  + frmt + '_' + typ \
                  + ('GEOM' if typ == 'allrounder' and allrounders_geom_mean else '') \
                  + '_' + str(adjusted_start_date.year) + '_' \
                  + str(adjusted_end_date.year) + '.png'

  Path(out_filename).parent.mkdir(exist_ok = True, parents = True)
  fig.savefig(out_filename)
  print("Written: " + out_filename)

