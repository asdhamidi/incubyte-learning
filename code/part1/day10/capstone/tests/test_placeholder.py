from pathlib import Path

SAMPLE = Path(__file__).resolve().parent.parent / "sample_data" / "games_sample.csv"


def test_sample_file_is_comma_separated_with_a_header():
    header = SAMPLE.read_text().splitlines()[0].split(",")
    assert header[0] == "id"
    assert len(header) == 16
