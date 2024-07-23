from matplotlib import pyplot as plt
from pathlib import Path

import numpy as np

ALLROUNDERS_GEOM_MEAN = False

def get_allrounder_rating(x, y):
  if ALLROUNDERS_GEOM_MEAN:
    return np.sqrt(x * y)
  else:
    return x * y / 1000

resolution = tuple([7.2, 7.2])
fig, ax = plt.subplots(figsize = resolution)

xax = range(0, 1000)
yax = range(0, 1000)

xy = np.array([get_allrounder_rating(x, y) for x in xax for y in yax]).reshape(1000, -1)

resolution = tuple([7.2, 7.2])
fig, ax = plt.subplots(figsize = resolution)

ax.set_title("All-Rounder Rating (" \
                  + ("geometric mean" if ALLROUNDERS_GEOM_MEAN else "classic") + ')', \
              fontsize = 'x-large')
ax.set_xlabel("Batting Rating", fontsize = 'x-large')
ax.set_ylabel("Bowling Rating", fontsize = 'x-large')

ax.set_xlim(0, 1000)
ax.set_ylim(0, 1000)

allticks = range(0, 1001, 100)
ax.set_xticks(allticks)
ax.set_xticklabels([str(x) for x in allticks], fontsize = 'large')
ax.set_yticks(allticks)
ax.set_yticklabels([str(y) for y in allticks], fontsize = 'large')

ax.grid(True, which = 'both', axis = 'both', alpha = 0.5, linestyle = ':', color = 'white')

plt.imshow(xy)

for x in range(100, 1000, 100):
  for y in range(100, 1000, 100):
    text = get_allrounder_rating(x, y)
    plt.text(x, y, s = '{v:3.0f}'.format(v = text), color = 'white', fontsize = 'large', \
              horizontalalignment = 'center', verticalalignment = 'center')

cbar_ticks = range(0, 1001, 100)
cbar = plt.colorbar(shrink = 0.7, aspect = 50, ticks = cbar_ticks)
cbar.set_label(label = 'All-Rounder Rating', size = 'x-large')
cbar.ax.set_yticklabels([str(t) for t in cbar_ticks], fontsize = 'large')

ax.contour(xy, levels = range(100, 1000, 100), colors = 'white', \
                alpha = 0.5, antialiased = True)

fig.tight_layout()

out_filename = 'out/images/heatmap/allrounder/' \
                + ("geometric" if ALLROUNDERS_GEOM_MEAN else "classic") \
                + '.png'
Path(out_filename).parent.mkdir(exist_ok = True, parents = True)

fig.savefig(out_filename)
print("Written: " + out_filename)
