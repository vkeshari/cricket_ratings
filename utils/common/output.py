from datetime import date, datetime

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
  