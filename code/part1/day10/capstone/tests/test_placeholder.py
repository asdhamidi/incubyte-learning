from pathlib import Path

SAMPLE = Path(__file__).resolve().parent.parent / "sample_data" / "games_sample.tsv"


def test_sample_file_is_tab_separated_with_a_header():
    header = SAMPLE.read_text().splitlines()[0].split("\t")
    assert header[0] == "id"
    assert len(header) == 16
