# cricket_ratings
Crawl data from ICC player rankings website and create animated graphs of player ratings over time.
[Warning] Code is semi-polished: It does the job but can be refactored to be more efficient and readable.

Recommended start dates by format:
test 1901-01-01 for data, 1951-01-01 for graphs (note: no international cricket was played during WW1 and WW2)
odi  1975-01-01 for data, 1981-01-01 for graphs
t20  2007-01-01 for data, 2009-01-01 for graphs

Recommended threshold for all bar charts: 500
Recommended thresholds for line charts:
+ Batting - Test: 750, ODI: 750, T20: 700
+ Bowling - Test: 700, ODI: 700, T20: 600
+ Country specific graph - 100 less than usual

Common Parameters:
+ FORMAT: ['test', 'odi', 't20']
+ TYPE: ['batting', 'bowling', 'allrounder'] (no 'allrounder' for get_data.py because those pages don't exist)
+ START_DATE / END_DATE: Self-explanatory.

'get_data.py'
Crawls ICC player ratings website for data and stores it in CSV format, one file per calendar day.
+ START_DATE: Start crawling data from this date. End date is always today's calendar date.

'build_players.py'
Reads stored ratings data from get_data.py and creates rating timelines, one file per player.
+ END_DATE  : Set it to the last date you have data for.
Known issue: Two test players from India are named Cottari Nayudu from 1934-01-09 to 1936-12-07. Data is overwritten.

'animate.py'
Reads player ratings timelines from build_players.py and creates an animated graph of ratings over time.
+ COUNTRY_PREFIX: Country code (e.g. AUS) or empty for all players.
+ MAX_RATING    : Maximum rating to show (y-axis max).
+ THRESHOLD     : Minimum rating to show (y-axis min).
+ Y_BUFFER      : Ratings are calculated for this buffer below the THRESHOLD but now shown.
+ GRAPH_SMOOTH  : Fit a monotonic spline curve on data
+ TITLE_POSITION: Show the current date on the graph at this y-axis (rating) value.

utils/
Note: Run these from the repository root folder.

'top_final_ratings.py'
Reads player ratings timelines from build_players.py and shows players that had the highest ratings at retirement.
+ MAX_PLAYERS: Self-explanatory

'time_at_top.py'
Reads player ratings timelines from build_players.py and shows players that were in the top N ratings for the longest time.
+ NUM_TOP    : Count days when player's rating is in the top NUM_TOP
+ MAX_PLAYERS: Self-explanatory
