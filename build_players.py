from datetime import date, timedelta
from pathlib import Path

# ['batting', 'bowling', 'allrounder']
TYPE = {'batting', 'bowling', 'allrounder'}
# ['test', 'odi', 't20']
FORMAT = 't20'

ONE_DAY = timedelta(days = 1)

START_DATE = date(2007, 1, 1)
# Last day of available data
END_DATE = date(2024, 7, 3)

assert not TYPE - {'batting', 'bowling', 'allrounder'}, "Invalid TYPE provided"
assert FORMAT in ['test', 'odi', 't20'], "Invalid FORMAT provided"
assert START_DATE < END_DATE, "START_DATE must be earlier than END_DATE"
assert END_DATE <= date.today(), "Future END_DATE requested"

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

def get_file_lines(filename):
  in_file = Path(filename)
  if not in_file.exists():
    print (filename + '\t' + 'NOT FOUND')
    return

  lines = []
  with in_file.open('r') as f:
    lines += f.readlines()

  return lines

def parse_date(d, typ, frmt, data):
  (yr, mn, dy) = date_to_parts(d)
  date_str = yr + mn + dy
  filename = 'data/' + typ + '/' + frmt + '/' + date_str + '.csv'
  lines = get_file_lines(filename)

  if not lines:
    return

  for l in lines:
    parts = l.strip().split(',')
    rank = eval(parts[0])
    rating = eval(parts[1])
    name = fix_name(parts[2])
    if (len(parts) > 4):
      for i in range(3, len(parts) - 1):
        name += '_' + fix_name(parts[i])
    country = parts[len(parts) - 1]

    key = country + ' ' + name
    if key not in data:
      data[key] = {}
      data[key]['country'] = country
      data[key]['name'] = name
      data[key]['ratings'] = {}
    data[key]['ratings'][date_str] = {}
    data[key]['ratings'][date_str]['rank'] = rank
    data[key]['ratings'][date_str]['rating'] = rating

  #print (typ + '\t' + frmt + '\t' + date_str + '\t' + str(len(data)) + ' players')

def validate_data(start_date, end_date, typ, frmt, data):
  print ('VALIDATING DATA: ' + frmt + '\t' + typ)

  date_to_count = {}
  for p in data:
    for d in data[p]['ratings']:
      if d not in date_to_count:
        date_to_count[d] = 0
      date_to_count[d] += 1
  print ('Dates built back: ' + str(len(date_to_count)))

  mismatch = False
  d = start_date
  while (d < end_date):
    (yr, mn, dy) = date_to_parts(d)
    date_str = yr + mn + dy
    filename = 'data/' + typ + '/' + frmt + '/' + date_str + '.csv'
    lines = get_file_lines(filename)

    failed = False
    if not lines:
      d += ONE_DAY
      continue
    if date_str not in date_to_count:
      mismatch = True
      print (date_str + ':\t' + 'NO PLAYER DATA FOUND')
      d += ONE_DAY
      continue

    original_count = len(lines)
    parsed_count = date_to_count[date_str]
    if not parsed_count == original_count:
      mismatch = True
      print (date_str + ':\t' + 'ORIGINAL: ' + str(original_count) + ',\t' \
              + 'PARSED: ' + str(parsed_count))

    d += ONE_DAY

  return True#not mismatch

def parse_all_dates(typ):
  player_data = {}
  d = START_DATE
  while (d < END_DATE):
    parse_date(d, typ, FORMAT, player_data)
    d += ONE_DAY

  if validate_data(START_DATE, END_DATE, typ, FORMAT, player_data):
    print ('VALIDATION SUCCESS')
    return player_data
  else:
    print ('VALIDATION FAILED')
    return {}

def build_allrounder_data(player_data_by_format):
  max_ever = 0
  batting_player_data = player_data_by_format['batting']
  bowling_player_data = player_data_by_format['bowling']
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

    # print (str(len(all_player_data)) + '\t' \
    #         + 'Max: ' + str(max_ever) + '\t' + key)

  return all_player_data

player_data_by_format = {}
for typ in ['batting', 'bowling']:
  if typ in TYPE or 'allrounder' in TYPE:
    player_data_by_format[typ] = parse_all_dates(typ)

for typ in TYPE:
  print ('\n' + FORMAT + '\t' + typ)

  if typ == 'allrounder':
    all_player_data = build_allrounder_data(player_data_by_format)
  else:
    all_player_data = player_data_by_format[typ]

  print ('Players built: ' + '\t' + str(len(all_player_data)))

  for key in all_player_data:
    country = all_player_data[key]['country']
    name = all_player_data[key]['name']
    ratings = all_player_data[key]['ratings']
    filename = 'players/' + typ + '/' + FORMAT + '/' + country + '_' + name + '.data'

    output_file = Path(filename)
    output_file.parent.mkdir(exist_ok = True, parents = True)

    with output_file.open('w') as f:
      for date_str in ratings:
        f.write(date_str + ',' \
                + str(all_player_data[key]['ratings'][date_str]['rank']) + ',' \
                + str(all_player_data[key]['ratings'][date_str]['rating']) + '\n')
      # print('\t' + filename + '\t' + str(len(all_player_data[key]['ratings'])))
  print(FORMAT + ' ' + typ + ' data written')

print ('\nAll data written')
