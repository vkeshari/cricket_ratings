# cricket_ratings
Crawl data from ICC player rankings website and create animated graphs of player ratings over time.
[Warning] Code is semi-polished: It does the job but can be refactored to be more efficient and readable.

Common Parameters:
+ FORMAT: ['test', 'odi', 't20']
+ TYPE: ['batting', 'bowling', 'allrounder'] (no 'allrounder' for get_data.py because those pages don't exist)
+ START_DATE / END_DATE: Self-explanatory.
+ ALLROUNDERS_GEOM_MEAN: Use an alternate formula that takes the geometric mean of batting and bowling ratings for a player as their allrounder rating.

Recommended start dates by format:
test 1901-01-01 for data, 1951-01-01 for graphs
odi  1975-01-01 for data, 1981-01-01 for graphs
t20  2007-01-01 for data, 2009-01-01 for graphs
Note: no international cricket was played during WW1 and WW2. It is recommended to skip years 1913-1920, 1940-1945 and 2020 for data analysis.

### Data ###

'get_data.py'
Crawls ICC player ratings website for data and stores it in CSV format, one file per calendar day.
+ START_DATE: Start crawling data from this date. End date is always today's calendar date.

'build_players.py'
Reads stored ratings data from get_data.py and creates rating timelines, one file per player.
+ END_DATE  : Set it to the last date you have data for.
Known issue: Two test players from India are named Cottari Nayudu from 1934-01-09 to 1936-12-07. Data is overwritten.

### Graphs ###
Recommended threshold for bar charts: 500
Recommended thresholds for line charts:
+ Batting - Test: 750, ODI: 750, T20: 700
+ Bowling - Test: 700, ODI: 700, T20: 600
+ Country specific graph - 100 less than usual
Recommended thresholds for all allrounder charts: 0

'rating_graph.py'
Reads player ratings timelines from build_players.py and creates an animated graph of ratings over time.
+ COUNTRY_PREFIX: Country code (e.g. AUS) or empty for all players.
+ MAX_RATING    : Maximum rating to show (y-axis max).
+ THRESHOLD     : Minimum rating to show (y-axis min).
+ Y_BUFFER      : Ratings are calculated for this buffer below the THRESHOLD but not shown.
+ GRAPH_SMOOTH  : Fit a monotonic spline curve on data
Bar charts only:
+ TOP_PLAYERS     : Total no. of bars shown
+ MIN_RATING_SCALE: Bars start at this value

'rating_histogram.py'
Reads player ratings timelines from build_players.py and created an animated histogram of rating distribution over time.
+ MAX_RATING: Maximum rating to show (x-axis max).
+ THRESHOLD : Minimum rating to show (x-axis min).
+ BIN_SIZE  : Group players into bins of this size on histogram.

Aggregation:
Aggregate ratings over a window by player or by bin using a numeric measure.
+ AGGREGATION_WINDOW: ['', 'monthly', 'quarterly', 'halfyearly', 'yearly', 'decadal'] (no aggregation if empty)
+ PLAYER_AGGREGATE  : ['', 'avg', 'median', 'min', 'max', 'first', 'last']
+ BIN_AGGREGATE     : ['', 'avg', 'median', 'min', 'max', 'first', 'last']

### Utils ###
./utils/*.py
Note: Run these from the repository root folder.
All utils read data from player ratings timelines created by build_players.py

'top_final_ratings.py'
Shows players that had the highest ratings at retirement.
+ MAX_PLAYERS: Self-explanatory

'time_at_top.py'
Shows players that were in the top N ratings for the longest time.
+ NUM_TOP: Count days when player's rating is in the top NUM_TOP

'single_day_changes.py'
Shows the largest single-day gains and drops in ratings.
+ NUM_TOP   : Show these many gains and drops in ratings
+ BIN_WIDTH : Show histogram of rating changes with bins of this width
+ MAX_CHANGE: Only show changes less than this value on histogram

Note: All utils below aggregate ratings over time windows.
Common aggregation params:
+ AGGREGATION_WINDOW: ['', 'monthly', 'quarterly', 'halfyearly', 'yearly', 'decadal']
+ PLAYER_AGGREGATE  : ['', 'avg', 'median', 'min', 'max', 'first', 'last']
+ BIN_AGGREGATE     : ['', 'avg', 'median', 'min', 'max', 'first', 'last']
+ CHANGED_DAYS_ONLY : Only aggregate over days when there was at least one change in ratings globally
+ SKIP_YEARS        : When calculating aggregates, skip these years when no or little international cricket was played (during WW1, WW2 and COVID-19)

+ SHOW_GRAPH       : Self-explanatory
+ GRAPH_CUMULATIVES: Calculate cumulative counts in each bin

+ SHOW_TOP_PLAYERS    : Self-explanatory
+ TOP_PLAYERS         : Only show these many top ranked players
+ BY_MEDAL_PERCENTAGES: Rank players by percentage of aggregation windows with each medal instead of counts
+ AVG_MEDAL_CUMULATIVE_COUNTS: Average no. of cumulative players for each medal

'top_ratings_graph.py' 
Aggregates each player's ratings over the specified time period, groups the players into cumulative bins by their rating for a range of all possible ratings, and then shows a graph of cumulative player counts by rating cutoff. Also calculates the most likely cutoffs for each medal.

'top_ratios_graph.py' 
Same as top_ratings_graph.py but uses players' rating ratio vs top rated player for calculations.
+ MIN_RATIO         : Lower limit of rating ratio for metrics and graph
+ MAX_RATIO         : Upper limit of rating ratio for metrics and graph
+ RATIO_STEP        : Show metrics and graph at this rating ratio increment
+ THRESHOLD_RELATIVE: Calculate players' rating ratios relative to THRESHOLD instead of to 0

'top_exp_graph.py'
Same as top_ratings_graph.py but uses a fitted exponential curve to aggregated ratings histogram before aggregating player ratings over bins by standard deviation (sigma) instead of ratings.
+ MIN_SIGMA   : Calculate player counts starting at this standard deviation value above THRESHOLD
+ MAX_SIGMA   : Calculate player counts up to this standard deviation value above THRESHOLD
+ EXP_BIN_SIZE: Split ratings into continuous bins of this size during counting

# DEPRECATED Utils #
'hist_aggregates.py'
Aggregates each bin of the histogram of rating distribution over the specified time period, then calculates mean and standard deviation for ratings assuming an exponential distribution of ratings.

'player_aggregates_exp.py'
Aggregates each player's ratings over the specified time period, then counts how many players fall into each standard deviation assuming exponential distribution of ratings.

'player_aggregates_ratio.py'
Aggregates each player's ratings over the specified time period, calculates their rating's ratio vs the top rated player, then groups the players into bins by their rating ratio.

'top_by_ratio.py'
Aggregates each player's ratings over the specified time period, calculates their rating's ratio vs the top rated player, groups the players into bins by their rating ratio, and then ranks the players by aggregation window counts where the player appears in bins of decreasing order of ratio values (the ratio values are cutoffs for medals).
