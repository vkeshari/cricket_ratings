from urllib import request
from datetime import date, timedelta

# ['batting', 'bowling']
TYPE = 'bowling'
# ['test', 'odi', 't20']
FORMAT = 'test'
START_YEAR = 1900

ID_TAG = 'td class="top100id"'
RATING_TAG = 'td class="top100rating"'
NAME_TAG = 'td class="top100name"'
NATION_TAG = 'td class="top100nation"'
CBR_TAG = 'td class="top100cbr"'

ONE_DAY = timedelta(days=1)

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
        + '?stattype=' + TYPE \
        + '&day=' + dy + '&month=' + mn + '&year=' + yr
  page = request.urlopen(url)
  text = page.read().decode('utf-8')
  return text

def parse_html(h):
  data = []
  pos = h.find(ID_TAG)
  while (pos != -1):
    pos = h.find(ID_TAG)
    h = h[pos:]
    pos = h.find('>')
    h = h[pos+1:]
    pos = h.find('<')
    rank = eval(h[:pos].strip())

    pos = h.find(RATING_TAG)
    h = h[pos:]
    pos = h.find('>')
    h = h[pos+1:]
    pos = h.find('<')
    rating = eval(h[:pos].strip())

    pos = h.find(NAME_TAG)
    h = h[pos:]
    pos = h.find('>')
    h = h[pos+1:]
    pos = h.find('>')
    h = h[pos+1:]
    pos = h.find('<')
    name = h[:pos].strip()

    pos = h.find(NATION_TAG)
    h = h[pos:]
    pos = h.find('title=')
    h = h[pos+7:]
    pos = h.find('"')
    nation = h[:pos].strip()

    data.append(str(rank) + ',' + str(rating) + ',' + name + ',' + nation + '\n')
    pos = h.find(ID_TAG)
  return data

def write_data(d, data):
  (yr, mn, dy) = date_to_parts(d)
  filename = 'data/' + TYPE + '/' + FORMAT + '/' + yr + mn + dy + '.csv'
  f = open(filename, 'w')
  for p in data:
    f.write(p)
  f.close()
  print('\t' + filename + '\t' + str(len(data)))

d = date(START_YEAR, 1, 1)
today = date.today()
while (d < today):
  t = get_data(d)
  c = parse_html(t)
  write_data(d, c)
  d += ONE_DAY

