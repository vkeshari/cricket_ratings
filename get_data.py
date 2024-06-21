from urllib import request
from pathlib import Path
from datetime import date, timedelta

# ['batting', 'bowling']
TYPE = ''
# ['test', 'odi', 't20']
FORMAT = ''

START_DATE = date(2007, 1, 1)
TODAY = date.today()
ONE_DAY = timedelta(days=1)

ID_TAG_PREFIX = '<td class="'
ID_TAG_START = '>'
ID_TAG_END = '</td>'

RATING_TAG_PREFIX = '<td class="'
RATING_TAG_START = '>'
RATING_TAG_END = '</td>'

NAME_TAG_PREFIX = 'class="players">'
NAME_TAG_START = '>'
NAME_TAG_END = '</a></td>'

NATION_TAG_PREFIX = 'alt="'
NATION_TAG_START = '"'
NATION_TAG_END = '">'

BURN_PREFIX = '<td class="'

def date_to_parts(d):
  yr = str(d.year)
  mn = str(d.month)
  if (d.month < 10):
    mn = '0' + mn
  dy = str(d.day)
  if (d.day < 10):
    dy = '0' + dy
  return (yr, mn, dy)

def get_data(d):
  (yr, mn, dy) = date_to_parts(d)
  print (yr + '\t' + mn + '\t' + dy)
  url = 'http://www.relianceiccrankings.com/datespecific/' + FORMAT + '/' \
        + TYPE  + '/' + yr + '/' + mn + '/' + dy + '/'
  page = request.urlopen(url)
  text = page.read().decode('utf-8')
  return text

def parse_html(h):
  data = []
  pos = h.find(ID_TAG_PREFIX)
  while (pos != -1):
    pos = h.find(ID_TAG_PREFIX)
    h = h[pos : ]
    start_pos = h.find(ID_TAG_START) + 1
    end_pos = h.find(ID_TAG_END)
    rank = eval(h[start_pos : end_pos].strip())
    h = h[end_pos : ]

    pos = h.find(RATING_TAG_PREFIX)
    h = h[pos : ]
    start_pos = h.find(RATING_TAG_START) + 1
    end_pos = h.find(RATING_TAG_END)
    rating = eval(h[start_pos : end_pos].strip())
    h = h[end_pos : ]

    pos = h.find(NAME_TAG_PREFIX)
    h = h[pos : ]
    start_pos = h.find(NAME_TAG_START) + 1
    end_pos = h.find(NAME_TAG_END)
    name = h[start_pos : end_pos].strip()

    pos = h.find(NATION_TAG_PREFIX)
    h = h[pos : ]
    start_pos = h.find(NATION_TAG_START) + 1
    end_pos = h.find(NATION_TAG_END)
    nation = h[start_pos : end_pos].strip()

    pos = h.find(BURN_PREFIX)
    h = h[pos + len(BURN_PREFIX) : ]

    player_text = str(rank) + ',' + str(rating) + ',' + name + ',' + nation
    data.append(player_text + '\n')

    pos = h.find(ID_TAG_PREFIX)
  return data

def write_data(d, data):
  (yr, mn, dy) = date_to_parts(d)
  filename = 'data/' + TYPE + '/' + FORMAT + '/' + yr + mn + dy + '.csv'

  output_file = Path(filename)
  output_file.parent.mkdir(exist_ok = True, parents = True)

  with output_file.open('w') as f:
    for p in data:
      f.write(p)
  print('\t' + filename + '\t' + str(len(data)))

d = START_DATE
while (d < TODAY):
  text = get_data(d)
  players = parse_html(text)

  if not players:
    print("\tNO PLAYERS FOUND")
    break

  write_data(d, c)
  d += ONE_DAY

