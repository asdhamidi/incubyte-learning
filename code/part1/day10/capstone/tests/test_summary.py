import csv

import pytest
from games_pipeline.load import build_staging, build_summary, load_raw, read_summary

STG_DDL = """
    CREATE TABLE stg_games (
        id VARCHAR, rated BOOLEAN, created_at_ms BIGINT,
        white_rating INTEGER, black_rating INTEGER, winner VARCHAR,
        victory_status VARCHAR, source_file VARCHAR, loaded_at TIMESTAMP
    )"""


def stage(con, *games):
    """Create stg_games from small hand-made games. Defaults: rated, white 1500 vs black 1500."""
    con.execute(STG_DDL)
    for i, game in enumerate(games):
        g = {
            "rated": True,
            "white_rating": 1500,
            "black_rating": 1500,
            "winner": "white",
            **game,
        }
        con.execute(
            "INSERT INTO stg_games VALUES (?, ?, 0, ?, ?, ?, 'mate', 'f.tsv', NULL)",
            [f"x{i}", g["rated"], g["white_rating"], g["black_rating"], g["winner"]],
        )


def summary(con):
    build_summary(con)
    return read_summary(con)


def game(gap, higher_wins=True, **extra):
    """A decided rated game where white is higher rated by `gap` points."""
    winner = "white" if higher_wins else "black"
    return {"white_rating": 1500 + gap, "black_rating": 1500, "winner": winner, **extra}


# --- the metric rules -------------------------------------------------------


def test_rate_is_the_share_of_games_won_by_the_higher_rated_player(con):
    stage(con, game(50), game(50), game(50, higher_wins=False))

    assert summary(con) == [("1-99", 3, 2, 66.7)]


def test_the_higher_rated_player_can_be_black(con):
    stage(
        con,
        {"white_rating": 1400, "black_rating": 1700, "winner": "black"},
        {"white_rating": 1400, "black_rating": 1700, "winner": "white"},
    )

    assert summary(con) == [("200-399", 2, 1, 50.0)]


def test_unrated_games_are_excluded(con):
    stage(con, game(50), game(50, rated=False))

    assert summary(con) == [("1-99", 1, 1, 100.0)]


def test_draws_are_excluded(con):
    stage(con, game(50), game(50, winner="draw"))

    assert summary(con) == [("1-99", 1, 1, 100.0)]


def test_games_with_equal_ratings_are_excluded(con):
    stage(con, game(50), game(0))

    assert summary(con) == [("1-99", 1, 1, 100.0)]


def test_games_with_a_missing_rating_are_excluded(con):
    stage(con, game(50), game(50, white_rating=None))

    assert summary(con) == [("1-99", 1, 1, 100.0)]


@pytest.mark.parametrize(
    ("gap", "band"),
    [
        (1, "1-99"),
        (99, "1-99"),
        (100, "100-199"),
        (199, "100-199"),
        (200, "200-399"),
        (399, "200-399"),
        (400, "400+"),
        (1200, "400+"),
    ],
)
def test_band_boundaries(con, gap, band):
    stage(con, game(gap))

    assert summary(con) == [(band, 1, 1, 100.0)]


def test_a_band_with_no_games_has_no_row(con):
    stage(con, game(50), game(500))

    assert [row[0] for row in summary(con)] == ["1-99", "400+"]


def test_rows_come_out_in_band_order(con):
    stage(con, game(500), game(250), game(150), game(50))

    assert [row[0] for row in summary(con)] == ["1-99", "100-199", "200-399", "400+"]


def test_the_rate_comes_from_counts_not_an_average_of_rates(con):
    # one band, 1 of 3 games won by the higher-rated player
    stage(con, game(50), game(60, higher_wins=False), game(70, higher_wins=False))

    _band, games, won, rate = summary(con)[0]

    assert (games, won) == (3, 1)
    assert rate == round(100.0 * won / games, 1)


def test_an_empty_staging_table_gives_an_empty_summary(con):
    stage(con)

    assert summary(con) == []


# --- the worked example from the metric definition --------------------------


def test_the_worked_example_gives_the_hand_checked_result(
    con, sample_path, tmp_path, loaded_at
):
    ids = {"g1000x", "g1002x", "g1003x", "g1011x", "g1023x"}
    lines = sample_path.read_text().splitlines()
    chosen = [lines[0]] + [ln for ln in lines[1:] if ln.split("\t")[0] in ids]
    path = tmp_path / "example.tsv"
    path.write_text("\n".join(chosen) + "\n")
    assert len(chosen) == 7  # header plus six delivered rows, one of them a duplicate

    load_raw(con, path, loaded_at)
    build_staging(con)

    assert summary(con) == [("200-399", 1, 1, 100.0), ("400+", 2, 0, 0.0)]


# --- the whole sample file, against an independent calculation --------------


def reference_summary(path):
    """The metric worked out in plain Python, as a check on the SQL."""
    bands = {"1-99": [0, 0], "100-199": [0, 0], "200-399": [0, 0], "400+": [0, 0]}
    seen = set()
    with path.open(newline="") as f:
        for row in csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
            if row["id"] in seen:
                continue
            seen.add(row["id"])
            white, black = int(row["white_rating"]), int(row["black_rating"])
            if row["rated"] != "True" or row["winner"] == "draw" or white == black:
                continue
            gap = abs(white - black)
            band = (
                "1-99"
                if gap < 100
                else "100-199"
                if gap < 200
                else "200-399"
                if gap < 400
                else "400+"
            )
            higher = "white" if white > black else "black"
            bands[band][0] += 1
            bands[band][1] += row["winner"] == higher
    return [
        (band, games, won, round(100.0 * won / games, 1))
        for band, (games, won) in bands.items()
        if games
    ]


def test_the_sample_file_matches_an_independent_calculation(staged_con, sample_path):
    assert summary(staged_con) == reference_summary(sample_path)


def test_counted_games_reconcile_with_staging(staged_con):
    counted = sum(row[1] for row in summary(staged_con))
    expected = staged_con.execute(
        """
        SELECT COUNT(*) FROM stg_games
        WHERE rated AND winner IN ('white', 'black') AND white_rating <> black_rating
        """
    ).fetchone()[0]

    assert counted == expected
