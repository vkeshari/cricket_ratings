# cricket_ratings
Crawl data from ICC player rankings website and create animated graphs of player ratings over time.
[Warning] Code is semi-polished: It does the job but can be refactored to be more efficient and readable.

Common Parameters:
+ FORMAT: ['test', 'odi', 't20']
+ TYPE: ['batting', 'bowling', 'allrounder']

'get_data.py'
Crawls ICC player ratings website for data and stores it in CSV format, one file per calendar day.
+ START_YEAR: Data will be crawled starting January 01 of this year. End date is always today's calendar date

'build_players.py'
Reads stored ratings data from get_data.py and creates rating timelines, one file per player.
+ START_YEAR: Data will be crawled starting January 01 of this year. End date is always today's calendar date
+ today: Set it to the last date you have data for

'animate.py'
Reads player ratings timelines from build_players.py and creates an animated graph of ratings over time.
+ COUNTRY_PREFIX: Country code (e.g. AUS) or empty for all players
+ MAX_RATING: Maximum rating to show (y-axis max)
+ THRESHOLD: Minimum rating to show (y-axis min)
+ Y_BUFFER: Ratings are calculated for this buffer below the THRESHOLD but now shown
+ TITLE_POSITION: Show the current date on the graph at this y-axis (rating) value
+ START_DATE / END_DATE: self-explanatory
