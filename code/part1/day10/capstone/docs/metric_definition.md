# Metric definition: higher_rated_win_rate_by_gap_band

| Field | Value |
|---|---|
| Name | `higher_rated_win_rate_by_gap_band` |
| Question it answers / decision | Do higher-rated players win more, and by how much as the gap grows? Decides whether ratings are predictive enough to base matchmaking on |
| Definition (one sentence) | Among decided rated games, the share won by the player with the higher rating, split by the size of the rating gap |
| Row grain | One row per game (`id`) |
| Output grain | One row per rating-gap band (1-99, 100-199, 200-399, 400+) |
| Numerator and denominator | Games won by the higher-rated player / decided rated games with different ratings, in the band |
| Filters and exclusions | Rated games only. Draws excluded. Games where both ratings are equal excluded. Duplicate deliveries of a game counted once |
| Time window (date field, time zone) | All games in the table. `created_at` (epoch milliseconds, UTC) is available to filter by period later |
| Edge cases | Equal ratings have no higher-rated player. A game delivered twice is one game. A band with no games has no row. Ratings are taken as recorded for the game |
| Source and owner | `stg_games`, built from the Lichess games file. Owner: the ratings or matchmaking owner who asked (to confirm) |
| Caveats | Draws are left out, so the rate is a share of decisive games. Small bands give noisy rates, so the game count sits next to every rate. The sample file is synthetic, so only the real file answers the question |

## Worked example
Six delivered rows from the sample file, checked by hand:

| id | Rated | White | Black | Winner | Higher-rated | Gap | Band | Counts? | Higher won? |
|---|---|---|---|---|---|---|---|---|---|
| g1000x | yes | 1431 | 2070 | white | black | 639 | 400+ | yes | no |
| g1002x | no | 1528 | 1171 | white | | | | no, unrated | |
| g1003x | yes | 2070 | 1328 | black | white | 742 | 400+ | yes, once | no |
| g1003x (again) | yes | 2070 | 1328 | black | | | | no, duplicate | |
| g1011x | yes | 2085 | 1784 | white | white | 301 | 200-399 | yes | yes |
| g1023x | yes | 1649 | 1203 | draw | | | | no, draw | |

Expected result for these six rows:

| Band | Games | Higher-rated won | Rate |
|---|---|---|---|
| 200-399 | 1 | 1 | 100.0% |
| 400+ | 2 | 0 | 0.0% |

Across all counted games, 1 of 3 was won by the higher-rated player (33.3%).

## Upset views: when does the lower-rated player win?
A follow-up to the main question. The same games are counted (`decided_games`: rated, decisive, two different ratings), and the rate is the share won by the lower-rated player, so it is 100% minus the higher-rated win rate for the same games. Each view shows the counts next to the rate, and each counts exactly the games `games_summary` counts.

| View | One row per | Rule |
|---|---|---|
| `upset_by_opening` | Opening family | The family is the opening name before the first colon, so every Sicilian Defense variation counts as the Sicilian Defense. A missing name is `unknown` |
| `upset_by_ending` | How the game ended | `victory_status`: mate, resign or out of time. A missing value is `unknown` |
| `upset_by_length` | Game length | `turns` (moves by both players) in four buckets: 1-30, 31-60, 61-90, 91+. A missing or unreadable value is `unknown` |

Caveats: openings with few games give noisy rates, so read the count first. An upset rate by opening or length shows an association, not a cause: for example, long games are more often upsets, but that does not mean a long game makes an upset likelier.

## Change log
| Date       | Change        | Why                |
| ---------- | ------------- | ------------------ |
| 2026-11-10 | First version | Capstone question  |
| 2026-11-13 | Added the three upset views | Follow-up: when does the lower-rated player win? |
