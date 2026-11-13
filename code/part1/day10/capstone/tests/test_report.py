from games_pipeline.report import bar, format_summary, format_upsets

SUMMARY = [("1-99", 4, 1, 25.0), ("100-199", 2, 1, 50.0)]


def test_a_bar_is_as_full_as_the_rate():
    assert bar(0) == "." * 20
    assert bar(50) == "#" * 10 + "." * 10
    assert bar(100) == "#" * 20


def test_a_bar_never_leaves_its_width():
    assert len(bar(100.0)) == len(bar(33.3)) == len(bar(0.0)) == 20


def test_the_summary_lists_each_band_and_the_overall_rate_from_the_counts():
    text = format_summary(SUMMARY)

    assert "1-99" in text and "100-199" in text
    assert "overall: 6 games, 2 won by the higher-rated player (33.3%)" in text


def test_an_empty_summary_says_so_instead_of_dividing_by_zero():
    assert "no games" in format_summary([])


def test_the_upset_tables_are_titled_and_the_openings_are_cut_to_the_top_few():
    openings = [(f"Opening {i}", 100 - i, 10, 10.0) for i in range(15)]

    text = format_upsets(
        {"opening": openings, "ending": [("mate", 4, 1, 25.0)], "length": []},
        top_openings=10,
    )

    assert "lower-rated player wins" in text
    assert "Opening 9" in text
    assert "Opening 10" not in text
    assert "5 more" in text
    assert "mate" in text
