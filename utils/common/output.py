from datetime import date, datetime, timedelta
from matplotlib import cm

import numpy as np

ONE_DAY = timedelta(days = 1)
ONE_YEAR = timedelta(days = 365)

def string_to_date(s):
  dt = datetime.strptime(s, '%Y%m%d')
  return date(dt.year, dt.month, dt.day)

def date_to_string(d):
  yr = str(d.year)
  mn = str(d.month)
  if (d.month < 10):
    mn = '0' + mn
  dy = str(d.day)
  if (d.day < 10):
    dy = '0' + dy
  return yr + '-' + mn + '-' + dy

def readable_name(p):
  sep = p.find('_')
  return p[sep + 1 : ].split('.')[0].replace('_', ' ')

def country(p):
  return p.split('_')[0]

def readable_name_and_country(p):
  return readable_name(p) + ' (' + country(p) + ')'

def last_name(p):
  return p.split('.')[0].split('_')[-1]

def get_player_colors(players, by_country = False):
  player_to_color = {}
  if by_country:
    country_colors = {'AFG': 'dodgerblue',
                      'AUS': 'yellow',
                      'BAN': 'forestgreen',
                      'BRM': 'rosybrown',
                      'CAN': 'crimson',
                      'EAF': 'goldenrod',
                      'ENG': 'cornflowerblue',
                      'HK': 'red',
                      'IND': 'blue',
                      'IRE': 'limegreen',
                      'KEN': 'darkgreen',
                      'NAM': 'steelblue',
                      'NED': 'darkorange',
                      'NZ': 'black',
                      'PAK': 'green',
                      'SA': 'lime',
                      'SCO': 'royalblue',
                      'SL': 'darkblue',
                      'UAE': 'dimgrey',
                      'WI': 'maroon',
                      'ZIM': 'orangered',
                      }
    for p in players:
      if country(p) in country_colors:
        player_to_color[p] = country_colors[country(p)]
      else:
        player_to_color[p] = 'darkgrey'
  else:
    color_stops = np.linspace(0, 1, len(players) + 1)
    colors = cm.turbo(color_stops)
    player_to_color = {p: colors[i] for i, p in enumerate(players)}

  return player_to_color


def get_timescale_xticks(start_date, end_date, format = 'square'):
  assert format in ['square', 'widescreen']
  if format == 'square':
    counts_to_yr_widths = {1: 1, 10: 2, 25: 5, 50: 10}
  elif format == 'widescreen':
    counts_to_yr_widths = {2: 1, 20: 2, 50: 5, 100: 10}

  xtick_yr_range = []
  for c in counts_to_yr_widths:
    if (end_date - start_date) > c * ONE_YEAR:
      xtick_yr_range = range(start_date.year, end_date.year + 1, counts_to_yr_widths[c])

  if xtick_yr_range:
    xticks = [date(yr, 1, 1) for yr in xtick_yr_range]
    xticklabels = [str(x.year) for x in xticks]
  else:
    xticks = []
    d = start_date
    while d <= end_date:
      if d.day == 1:
        xticks.append(d)
      d += ONE_DAY
    xticklabels = [str(x.year) + '-' + str(x.month) for x in xticks]
  
  return xticks, xticklabels
