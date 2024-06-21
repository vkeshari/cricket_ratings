from datetime import date, timedelta
from pathlib import Path

# ['batting', 'bowling', 'allrounder']
TYPE = ''
# ['test', 'odi', 't20']
FORMAT = ''

ONE_DAY = timedelta(days=1)

START_DATE = date(2001, 1, 1)
# Last day of data available
END_DATE = date.today() - 0 * ONE_DAY

def date_to_parts(d):
  yr = str(d.year)
  mn = str(d.month)
  if (d.month < 10):
    mn = '0' + mn
  dy = str(d.day)
  if (d.day < 10):
    dy = '0' + dy
  return (yr, mn, dy)

def fix_name(name):
  return name.strip() \
              .replace('.', '_') \
              .replace(' ', '_') \
              .replace("'", '_')

def parse_date(d, typ, data):
  (yr, mn, dy) = date_to_parts(d)
  date_str = yr + mn + dy
  filename = 'data/' + typ + '/' + FORMAT + '/' + date_str + '.csv'
  f = open(filename, 'r')
  lines = f.readlines()
  f.close()

  for l in lines:
    parts = l.strip().split(',')
    rank = eval(parts[0])
    rating = eval(parts[1])
    name = fix_name(parts[2])
    if (len(parts) > 4):
      for i in range(3, len(parts)-1):
        name += '_' + fix_name(parts[i])
    country = parts[len(parts)-1]

    key = country + ' ' + name
    if key not in data:
      data[key] = {}
      data[key]['country'] = country
      data[key]['name'] = name
      data[key]['ratings'] = {}
    data[key]['ratings'][date_str] = {}
    data[key]['ratings'][date_str]['rank'] = rank
    data[key]['ratings'][date_str]['rating'] = rating

  print (typ + '\t' + date_str + '\t' + str(len(data)))

def parse_all_dates(typ):
  player_data = {}
  d = START_DATE
  while (d < END_DATE):
    parse_date(d, typ, player_data)
    d += ONE_DAY
  return player_data

def build_allrounder_data():
  max_ever = 0
  batting_player_data = parse_all_dates('batting')
  bowling_player_data = parse_all_dates('bowling')
  all_player_data = {}
  for key in batting_player_data:
    if key not in bowling_player_data:
      continue
    all_player_data[key] = {}
    all_player_data[key]['country'] = batting_player_data[key]['country']
    all_player_data[key]['name'] = batting_player_data[key]['name']
    all_player_data[key]['ratings'] = {}
    d = START_DATE
    while d < END_DATE:
      (yr, mn, dy) = date_to_parts(d)
      date_str = yr + mn + dy
      if date_str in batting_player_data[key]['ratings'] \
          and date_str in bowling_player_data[key]['ratings']:
        batting_rating = batting_player_data[key]['ratings'][date_str]['rating']
        bowling_rating = bowling_player_data[key]['ratings'][date_str]['rating']
        all_player_data[key]['ratings'][date_str] = {}
        all_player_data[key]['ratings'][date_str]['rank'] = 0
        rating = int(batting_rating * bowling_rating / 1000)
        if rating > max_ever:
          max_ever = rating
        all_player_data[key]['ratings'][date_str]['rating'] = rating
      d += ONE_DAY

    if len(all_player_data[key]['ratings']) == 0:
      del all_player_data[key]

    print (TYPE + '\t' + str(len(all_player_data)) + '\t' \
            + 'Max: ' + str(max_ever) + '\t' + key)

  return all_player_data

print (FORMAT + '\t' + TYPE)

if TYPE == 'allrounder':
  all_player_data = build_allrounder_data()
else:
  all_player_data = parse_all_dates(TYPE)

print ('All data parsed')
print ('Players: ' + '\t' + str(len(all_player_data)))

for key in all_player_data:
  country = all_player_data[key]['country']
  name = all_player_data[key]['name']
  ratings = all_player_data[key]['ratings']
  filename = 'players/' + TYPE + '/' + FORMAT + '/' + country + '_' + name + '.data'

  output_file = Path(filename)
  output_file.parent.mkdir(exist_ok = True, parents = True)

  with output_file.open('w') as f:
    for date_str in ratings:
      f.write(date_str + ',' \
              + str(all_player_data[key]['ratings'][date_str]['rank']) + ',' \
              + str(all_player_data[key]['ratings'][date_str]['rating']) + '\n')
  print('\t' + filename + '\t' + str(len(all_player_data[key]['ratings'])))
