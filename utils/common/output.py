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


def pretty_format(frmt, typ = ''):
  s = ''
  if frmt == 'test':
    s += "Test"
  elif frmt == 'odi':
    s += "ODI"
  elif frmt == 't20':
    s += "T20I"

  if typ == 'batting':
    s += " Batsmen"
  elif typ == 'bowling':
    s += " Bowlers"
  elif typ == 'allrounder':
    s += " All-Rounders"
  elif not typ:
    s += 's'

  return s


def readable_name(p):
  sep = p.find('_')
  return p[sep + 1 : ].split('.')[0].replace('_', ' ')

def last_name(p):
  return p.split('.')[0].split('_')[-1]

def country(p):
  return p.split('_')[0]

def readable_name_and_country(p):
  return readable_name(p) + ' (' + country(p) + ')'

def get_type_color(typ):
  assert typ in {'batting', 'bowling', 'allrounder'}
  if typ == 'batting':
    return 'blue'
  elif typ == 'bowling':
    return 'red'
  elif typ == 'allrounder':
    return 'green'

def get_colors_from_scale(num_colors, scale = cm.brg):
  color_stops = np.linspace(0, 1, num_colors + 1)
  return scale(color_stops)

def get_player_colors(players, by_country = False):
  player_to_color = {}
  if by_country:
    country_colors = {'AFG': 'dodgerblue',
                      'AUS': 'gold',
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
    colors = get_colors_from_scale(len(players))
    player_to_color = {p: colors[i] for i, p in enumerate(players)}

  return player_to_color


def resolution_by_span(start_date, end_date):
  if (end_date.year - start_date.year > 50):
    resolution = tuple([12.8, 7.2])
    aspect_ratio = 'widescreen'
  else:
    resolution = tuple([7.2, 7.2])
    aspect_ratio = 'square'
  return resolution, aspect_ratio


def get_timescale_xticks(start_date, end_date, format = 'square'):
  assert format in ['square', 'widescreen']

  xticks_major, xticks_minor = [], []
  date_range = end_date - start_date

  d = start_date
  while d <= end_date:
    if format == 'square' and date_range < ONE_YEAR or \
        format == 'widescreen' and date_range < 2 * ONE_YEAR:
      if d.day == 1 and d.month % 3 == 1:
        xticks_major.append(d)
      if d.day == 1:
        xticks_minor.append(d)
    elif format == 'square' and date_range < 2 * ONE_YEAR or \
        format == 'widescreen' and date_range < 5 * ONE_YEAR:
      if d.day == 1 and d.month % 6 == 1:
        xticks_major.append(d)
      if d.day == 1:
        xticks_minor.append(d)
    elif format == 'square' and date_range < 5 * ONE_YEAR or \
        format == 'widescreen' and date_range < 10 * ONE_YEAR:
      if d.day == 1 and d.month == 1:
        xticks_major.append(d)
      if d.day == 1:
        xticks_minor.append(d)
    elif format == 'square' and date_range < 10 * ONE_YEAR or \
        format == 'widescreen' and date_range < 20 * ONE_YEAR:
      if d.day == 1 and d.month == 1:
        xticks_major.append(d)
      if d.day == 1 and d.month % 3 == 1:
        xticks_minor.append(d)
    elif format == 'square' and date_range < 25 * ONE_YEAR or \
        format == 'widescreen' and date_range < 50 * ONE_YEAR:
      if d.day == 1 and d.month == 1 and d.year % 2 == 0:
        xticks_major.append(d)
      if d.day == 1 and d.month == 1:
        xticks_minor.append(d)
    elif format == 'square' and date_range < 50 * ONE_YEAR or \
        format == 'widescreen' and date_range < 100 * ONE_YEAR:
      if d.day == 1 and d.month == 1 and d.year % 5 == 0:
        xticks_major.append(d)
      if d.day == 1 and d.month == 1:
        xticks_minor.append(d)
    else:
      if d.day == 1 and d.month == 1 and d.year % 10 == 0:
        xticks_major.append(d)
      if d.day == 1 and d.month == 1:
        xticks_minor.append(d)

    d += ONE_DAY

  if format == 'square' and date_range < 2 * ONE_YEAR or \
        format == 'widescreen' and date_range < 5 * ONE_YEAR:
    xticklabels = [datetime.combine(d, datetime.min.time()).strftime("%b-%Y") \
                          for d in xticks_major]
  else:
    xticklabels = [str(x.year) for x in xticks_major]

  return xticks_major, xticks_minor, xticklabels
