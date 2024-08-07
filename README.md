# Cricket Ratings Analytics Library

> [!IMPORTANT]
> You may use the code in this repository for your own analysis of cricket ratings data, but:
> **You must attribute references to this or any derivative work to the original author**.

> [!TIP]
> Head over to the [Wiki](https://github.com/vkeshari/cricket_ratings/wiki) for detailed reports on:
> * **A Deep-Dive into ICC Player Rankings**, and 
> * **The Greatest Players of All-Time**.
> > _Last Updated: July 2024_

The Cricket Ratings Analytics Library can:
* Crawl data from ICC player rankings website
* Create static or animated graphs of player ratings over time
* Analyse and visualise changes in ratings over time
* Compare players based on rankings and ratings
* Aggregate metrics over time and create various graphs for aggregated metrics
* Find the top players from aggregated metrics

### Common Parameters:
+ `FORMAT`: `['test', 'odi', 't20']`
+ `TYPE`  : `['batting', 'bowling', 'allrounder']` (no `'allrounder'` option for `get_data.py` because those pages don't exist)
+ `START_DATE / END_DATE`: Self-explanatory.
+ `ALLROUNDERS_GEOM_MEAN`: Use an alternate formula that takes the geometric mean of batting and bowling ratings for a player as their allrounder rating.

### Recommended start dates by format:

+ `test`: `1901-01-01` for data, `1951-01-01` for graphs
+ `odi` : `1975-01-01` for data, `1981-01-01` for graphs
+ `t20` : `2007-01-01` for data, `2009-01-01` for graphs

> [!NOTE]
> No international cricket was played during WW1 and WW2. It is recommended to skip years `1913-1920`, `1940-1945` and `2020` for data analysis.

## Data

### `get_data.py`
Crawls ICC player ratings website for data and stores it in CSV format under `data/`, one file per calendar day.
+ `START_DATE`: Start crawling data from this date. End date is always today's calendar date.

### `build_players.py`
Reads stored ratings data in `data/` and creates rating timelines under `players/`, one file per player.
+ `END_DATE`  : Set it to the last date you have data for.
+ `VALIDATION`: Validate that built player data in `players/` matches raw data in `data/`

> [!CAUTION]
> **Known issue:** Two test players from India are named Cottari Nayudu from `1934-01-09` to `1936-12-07`. Data is overwritten if validation is skipped.

## Graphs

Recommended threshold for bar charts: `500`

Recommended thresholds for line charts:
+ Batting - Test: `750`, ODI: `750`, T20: `700`
+ Bowling - Test: `700`, ODI: `700`, T20: `600`
+ Country specific graph - `100` less than usual

Recommended thresholds for all allrounder charts: `0`

### `rating_graph.py`
Reads player ratings timelines from `players/` and creates an animated graph of ratings over time.
+ `COUNTRY_PREFIX`: Country code (e.g. AUS) or empty for all players.
+ `MAX_RATING`    : Maximum rating to show (y-axis max).
+ `THRESHOLD`     : Minimum rating to show (y-axis min).
+ `Y_BUFFER`      : Ratings are calculated for this buffer below the THRESHOLD but not shown.
+ `GRAPH_TYPE`    : `line` or `bar`
+ `GRAPH_SMOOTH`  : Fit a monotonic spline curve on data

Bar charts only:
+ `TOP_PLAYERS`     : Total no. of bars shown
+ `MIN_RATING_SCALE`: Bars start at this value

### `rating_histogram.py`
Reads player ratings timelines from `players/` and created an animated histogram of rating distribution over time.
+ `MAX_RATING`: Maximum rating to show (x-axis max).
+ `THRESHOLD` : Minimum rating to show (x-axis min).
+ `BIN_SIZE`  : Group players into bins of this size on histogram.

#### Aggregation
Aggregate ratings over a window by player or by bin using a numeric measure.

+ `AGGREGATION_WINDOW`: `['', 'monthly', 'quarterly', 'halfyearly', 'yearly', 'decadal']` (no aggregation if empty)
+ `PLAYER_AGGREGATE`  : `['', 'avg', 'median', 'min', 'max', 'first', 'last']`
+ `BIN_AGGREGATE`     : `['', 'avg', 'median', 'min', 'max', 'first', 'last']`

## Utils
`./utils/*.py`
> [!NOTE]
> Run all utils from the repository root folder.
>
> All utils except the first one read data from player ratings timelines in `players/`

> [!TIP]
> Many utils can iterate over multiple `FORMAT`s and `TYPE`s if any of these fields is left blank. See params for each util to learn more.

### `allrounder_heatmap.py`
Simple util for showing a heatmap of allrounder ratings as a function of batting and bowling ratings.

### `data_points.py`
Show total no. of data points by year or by decade.
+ `CHANGED_DAYS_CRITERIA`: Only consider days when Rating or Rank changed.

### `heartbeat.py`
Show every day with a ratings change for each format and type on one graph.

### `final_ratings.py`
Shows players that had the highest ratings at retirement.
+ `MAX_PLAYERS`  : Self-explanatory
+ `BY_FINAL_RANK`: Sort by final rank instead of final rating

### `single_player_ratings.py`
Show list of ratings for a single player.
+ `PLAYER`: Player name (in filename format)

### `player_competition.py`
Show the biggest competitors for a player: Players who were above or below the player's ratings, or their contemporaries, for the longest time.
+ `LOCATION`: `above` or `below` ratings, or `total` no. of days together on ratings list.

### `best_players.py`
Shows players that were in the top N ratings for the longest time, or with the highest all-time ratings.
+ `NUM_TOP`   : Count days when player's rating is in the top NUM_TOP
+ `SHOW_TABLE`: Self-explanatory

+ `SHOW_GRAPH`: Self-explanatory
+ `COLOR_BY_COUNTRY`: If graph is requested, color each player in their usual country colors.
+ `MAX_NAMES` : If graph is requested, show names for these many top players.

+ `SORT_BY_TIME_AT_TOP`: _(Choose One)_
+ `SORT_BY_MAX_RATING` : _(Choose One)_ (Graph not supported)

### `compare_players.py`
Compare two or more players over time by name or by rank.
+ `COMPARE_PLAYERS`: _(Choose One)_ Compare these players. See filenames under `players/*/*` for format.
+ `COMPARE_RANKS`  : _(Choose One)_ Compare players who are at these ranks at any time.

+ `PLOT_AVERAGES`    : Plot averages over this window size.
+ `PLOT_AVERAGE_KEYS`: Plot averages for these keys from `COMPARE_PLAYERS` or `COMPARE_RANKS` only.
+ `SHOW_CHANGES`     : Show single-day changes on graph.

### `single_day_changes.py`
Shows the largest single-day gains and drops in ratings.
+ `NUM_TOP`   : Show these many gains and drops in ratings
+ `BIN_WIDTH` : Show histogram of rating changes with bins of this width
+ `MAX_CHANGE`: Only show changes less than this value on histogram

### `aggregate_changes.py`
Shows aggregate statistics on single-day changes.
+ `REMOVE_MISSED_GAME_DROPS`: Remove drops that might have been due to missed games.
+ `SUSPICION_RANGE`: Consider rating drop percentages that are this amount around expected drop for missed games as suspicious.

## Aggregation Utils

> [!NOTE]
> All utils below aggregate ratings over time windows.

### Common aggregation params
+ `AGGREGATION_WINDOW`: `['', 'monthly', 'quarterly', 'halfyearly', 'yearly', 'decadal']`
+ `PLAYER_AGGREGATE`  : `['', 'avg', 'median', 'min', 'max', 'first', 'last']`
+ `CHANGED_DAYS_CRITERIA` : Only aggregate over days when there was at least one change in ratings, ranks, either or both globally
+ `SKIP_YEARS`        : When calculating aggregates, skip these years when no or little international cricket was played (during WW1, WW2 and COVID-19)

#### Debug bin counts
+ `SHOW_BIN_COUNTS`: Show counts for each aggregation window in each bin in range of metric used for scoring

#### Show top players by stats
+ `SHOW_TOP_STATS`: Show a table of top players by stats over metric used for scoring
+ `TOP_STATS_SORT`: Sort top stats table by these columns

#### Show top players by medals
+ `SHOW_TOP_MEDALS`     : Show a table of top players by medals awarded
+ `BY_MEDAL_PERCENTAGES`: Rank players by percentage of aggregation windows with each medal instead of counts
+ `AVG_MEDAL_CUMULATIVE_COUNTS`: Average no. of cumulative players for each medal

#### Show graph
+ `SHOW_GRAPH`        : Self-explanatory
+ `SHOW_MEDALS`       : Show medal thresholds on graph
+ `TRIM_EMPTY_ROWS`   : Remove rows from the top that have zero players
+ `TRUNCATE_GRAPH_AT` : Only show part of the graph up to threshold for this medal type
+ `GRAPH_CUMULATIVES` : Calculate cumulative counts in each bin

#### Table config
+ `TOP_PLAYERS`         : Only show these many top ranked players in tables

### `top_ratings_intervals.py`
Aggregates each player's ratings over the specified time period, groups the players into cumulative bins by their rating for a range of all possible ratings, and then shows a graph of cumulative player counts by rating cutoff. Also calculates the most likely cutoffs for each medal.

### `top_ratios_intervals.py`
Same as `top_ratings_intervals.py` but uses players' rating ratio vs top rated player for calculations.
+ `MIN_RATIO`         : Lower limit of rating ratio for metrics and graph
+ `MAX_RATIO`         : Upper limit of rating ratio for metrics and graph
+ `RATIO_STEP`        : Show metrics and graph at this rating ratio increment
+ `THRESHOLD_RELATIVE`: Calculate players' rating ratios relative to `THRESHOLD` instead of to `0`

### `top_normal_intervals.py`
Same as `top_ratings_intervals.py` but rescales aggregated player ratings to a normal distribution a before over bins by standard deviation (sigma) for calculations.
+ `MIN_SIGMA`    : Calculate player counts starting at this standard deviation value above `THRESHOLD`
+ `MAX_SIGMA`    : Calculate player counts up to this standard deviation value above `THRESHOLD`
+ `SIGMA_STEP`   : Show metrics and graph at this sigma increment

### `top_exp_intervals.py`
Same as `top_normal_intervals.py` but fits an exponential curve to aggregated ratings histogram before aggregating player ratings over histogram bins by standard deviation (sigma) for calculations.
+ `EXP_BIN_SIZE` : Split ratings into continuous bins of this size during counting
+ `BIN_AGGREGATE`: `['', 'avg', 'median', 'min', 'max', 'first', 'last']`

## Graph and Stats Utils

### `single_day_graph.py` and `single_day_histogram.py`
Show top ratings or distribution of ratings on a single day.

### `single_window_dist_histogram.py`
Show distribution of ratings aggregated over a single time window, or multiple windows but one-at-a-time.

### `single_window_dist_fit.py`
Try to fit a probaility distribution to ratings aggregated over a single time window.

### `multi_window_dist_heatmap.py` and `multi_window_dist_intervals.py`
Show a heatmap or interval graph of distribution of ratings aggregated over multiple time windows.

### `multi_window_dist_ratings.py` and `multi_window_dist_percentiles.py`
Show a distribution of what ratings various percentiles lie at, or which percentiles various ratings are at, for a multi-window rating aggregation.

### `top_ratings_chart.py` and `top_ratios_chart.py`
Do the same calculations as `top_ratings_intervals.py` and `top_ratios_intervals.py` respectively, but instead of showing an interval graph, show top N players for each year.

## DEPRECATED Utils
> [!CAUTION]
> There is no guarantee that these will run or produce accurate results.

### `hist_aggregates.py`
Aggregates each bin of the histogram of rating distribution over the specified time period, then calculates mean and standard deviation for ratings assuming an exponential distribution of ratings.

### `player_aggregates_exp.py`
Aggregates each player's ratings over the specified time period, then counts how many players fall into each standard deviation assuming exponential distribution of ratings.

### `player_aggregates_ratio.py`
Aggregates each player's ratings over the specified time period, calculates their rating's ratio vs the top rated player, then groups the players into bins by their rating ratio.

### `top_by_ratio.py`
Aggregates each player's ratings over the specified time period, calculates their rating's ratio vs the top rated player, groups the players into bins by their rating ratio, and then ranks the players by aggregation window counts where the player appears in bins of decreasing order of ratio values (the ratio values are cutoffs for medals).

### `top_clustering.py`
Shows results for 1-d clustering with kernel density estimation and gaussian mixture models for each aggregation window.
