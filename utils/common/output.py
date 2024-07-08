from datetime import date, datetime
from matplotlib import cm

import numpy as np

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
