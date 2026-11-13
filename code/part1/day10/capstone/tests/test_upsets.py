import pytest
from games_pipeline.load import (
    build_staging,
    build_summary,
    build_upset_views,
    read_summary,
    read_upsets,
)

# The upset views answer: when does the lower-rated player win? They use the same rules as
# games_summary (rated, decisive, unequal ratings), so every view counts the same games.

STG_DDL = """
    CREATE TABLE stg_games (
        id VARCHAR, rated BOOLEAN, created_at_ms BIGINT,
        white_rating INTEGER, black_rating INTEGER, winner VARCHAR,
        victory_status VARCHAR, turns INTEGER, opening_name VARCHAR,
        source_file VARCHAR, loaded_at TIMESTAMP
    )"""


def stage(con, *games):
    """Hand-made games. Defaults: rated, white 1600 vs black 1500, white wins by mate."""
    con.execute(STG_DDL)
    for i, game in enumerate(games):
        g = {
            "rated": True,
            "white_rating": 1600,
            "black_rating": 1500,
            "winner": "white",
            "victory_status": "mate",
            "turns": 40,
            "opening_name": "Opening A",
            **game,
        }
        con.execute(
            "INSERT INTO stg_games VALUES (?, ?, 0, ?, ?, ?, ?, ?, ?, 'f.csv', NULL)",
            [
                f"x{i}",
                g["rated"],
                g["white_rating"],
                g["black_rating"],
                g["winner"],
                g["victory_status"],
                g["turns"],
                g["opening_name"],
            ],
        )


def upsets(con, which):
    build_upset_views(con)
    return read_upsets(con)[which]


def upset(**extra):
    """The lower-rated player (black) wins."""
    return {"winner": "black", **extra}


def favourite(**extra):
    """The higher-rated player (white) wins."""
    return {"winner": "white", **extra}


# --- by opening -------------------------------------------------------------


def test_the_upset_rate_by_opening_is_the_share_won_by_the_lower_rated_player(con):
    stage(con, upset(), favourite(), favourite(), favourite())

    assert upsets(con, "opening") == [("Opening A", 4, 1, 25.0)]


def test_variations_of_an_opening_count_as_one_family(con):
    stage(
        con,
        upset(opening_name="Sicilian Defense: Najdorf Variation"),
        favourite(opening_name="Sicilian Defense: Dragon Variation"),
        favourite(opening_name="Sicilian Defense"),
    )

    assert upsets(con, "opening") == [("Sicilian Defense", 3, 1, 33.3)]


def test_a_missing_opening_name_is_reported_as_unknown(con):
    stage(con, upset(opening_name=None))

    assert upsets(con, "opening") == [("unknown", 1, 1, 100.0)]


def test_openings_come_out_with_the_most_played_first(con):
    stage(
        con,
        favourite(opening_name="Rare"),
        favourite(opening_name="Common"),
        favourite(opening_name="Common"),
    )

    assert [row[0] for row in upsets(con, "opening")] == ["Common", "Rare"]


def test_the_lower_rated_player_can_win_as_white_or_black(con):
    stage(
        con,
        {"white_rating": 1400, "black_rating": 1700, "winner": "white"},  # white upset
        {"white_rating": 1700, "black_rating": 1400, "winner": "black"},  # black upset
        {"white_rating": 1700, "black_rating": 1400, "winner": "white"},  # favourite
    )

    assert upsets(con, "opening") == [("Opening A", 3, 2, 66.7)]


# --- by how the game ended --------------------------------------------------


def test_the_upset_rate_by_ending_groups_by_victory_status(con):
    stage(
        con,
        upset(victory_status="mate"),
        favourite(victory_status="mate"),
        upset(victory_status="resign"),
        upset(victory_status="outoftime"),
        favourite(victory_status="outoftime"),
        favourite(victory_status="outoftime"),
    )

    assert upsets(con, "ending") == [
        ("outoftime", 3, 1, 33.3),
        ("mate", 2, 1, 50.0),
        ("resign", 1, 1, 100.0),
    ]


# --- by game length ---------------------------------------------------------


@pytest.mark.parametrize(
    ("turns", "bucket"),
    [
        (1, "1-30"),
        (30, "1-30"),
        (31, "31-60"),
        (60, "31-60"),
        (61, "61-90"),
        (90, "61-90"),
        (91, "91+"),
        (300, "91+"),
        (None, "unknown"),
    ],
)
def test_game_length_bucket_boundaries(con, turns, bucket):
    stage(con, upset(turns=turns))

    assert upsets(con, "length") == [(bucket, 1, 1, 100.0)]


def test_game_lengths_come_out_shortest_first_and_unknown_last(con):
    stage(con, favourite(turns=120), favourite(turns=None), favourite(turns=10))

    assert [row[0] for row in upsets(con, "length")] == ["1-30", "91+", "unknown"]


# --- the metric rules are the same as the summary ---------------------------


@pytest.mark.parametrize("which", ["opening", "ending", "length"])
@pytest.mark.parametrize(
    "excluded",
    [
        {"rated": False},
        {"winner": "draw"},
        {"white_rating": 1500, "black_rating": 1500},
        {"white_rating": None},
    ],
)
def test_unrated_drawn_equal_and_unrated_games_are_left_out(con, which, excluded):
    stage(con, upset(), excluded)

    assert upsets(con, which)[0][1:3] == (1, 1)


def test_the_rate_comes_from_counts(con):
    stage(con, upset(), favourite(), favourite())

    _name, games, won, rate = upsets(con, "opening")[0]

    assert (games, won) == (3, 1)
    assert rate == round(100.0 * won / games, 1)


def test_empty_staging_gives_empty_views(con):
    stage(con)
    build_upset_views(con)

    assert read_upsets(con) == {"opening": [], "ending": [], "length": []}


def test_the_views_follow_staging_without_being_rebuilt(con):
    stage(con, upset())
    build_upset_views(con)

    con.execute(
        "INSERT INTO stg_games VALUES "
        "('late', TRUE, 0, 1600, 1500, 'white', 'mate', 40, 'Opening A', 'f.csv', NULL)"
    )

    assert read_upsets(con)["opening"] == [("Opening A", 2, 1, 50.0)]


# --- the whole sample file, against the summary -----------------------------


@pytest.mark.parametrize("which", ["opening", "ending", "length"])
def test_every_view_counts_the_same_games_as_the_summary(staged_con, which):
    build_summary(staged_con)
    build_upset_views(staged_con)
    summary = read_summary(staged_con)
    counted = sum(row[1] for row in summary)
    higher_won = sum(row[2] for row in summary)

    rows = read_upsets(staged_con)[which]

    assert sum(row[1] for row in rows) == counted
    assert sum(row[2] for row in rows) == counted - higher_won


def test_the_sample_file_shows_its_opening_families(staged_con):
    build_upset_views(staged_con)

    families = {row[0] for row in read_upsets(staged_con)["opening"]}

    assert "Scandinavian Defense" in families
    assert not any(":" in family for family in families)


def test_staging_carries_turns_and_the_opening_name(raw_con):
    build_staging(raw_con)

    row = raw_con.execute(
        "SELECT turns, opening_name FROM stg_games WHERE id = 'g1000x'"
    ).fetchone()

    assert row == (80, "Scandinavian Defense: Mieses-Kotroc Variation")


def test_a_turns_value_that_is_not_a_number_becomes_missing_not_an_error(raw_con):
    raw_con.execute("UPDATE raw_games SET turns = 'many' WHERE id = 'g1000x'")

    build_staging(raw_con)

    assert raw_con.execute(
        "SELECT turns FROM stg_games WHERE id = 'g1000x'"
    ).fetchone() == (None,)
