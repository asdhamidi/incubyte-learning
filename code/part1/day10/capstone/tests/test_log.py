import io
import logging

import pytest
from games_pipeline.log import configure_logging, step


@pytest.fixture
def output():
    """Send the pipeline's log to a string for the test, and restore logging afterwards."""
    stream = io.StringIO()
    root = logging.getLogger()
    before = list(root.handlers), root.level
    configure_logging(stream=stream, color=False)
    yield stream
    root.handlers[:], root.level = before


def test_a_line_is_a_time_and_the_message_without_the_level_or_logger_name(output):
    logging.getLogger("games_pipeline.something").info("raw has 20058 rows")

    line = output.getvalue().strip()

    assert line.endswith("raw has 20058 rows")
    assert "INFO" not in line
    assert "games_pipeline" not in line
    assert line[2] == ":" and line[5] == ":"  # HH:MM:SS


def test_the_verbose_log_names_the_module(output):
    configure_logging(verbose=True, stream=output, color=False)
    logging.getLogger("games_pipeline.something").debug("detail")

    assert "games_pipeline.something" in output.getvalue()


def test_a_step_shows_when_it_starts_and_when_it_is_done_with_its_time(output):
    with step(logging.getLogger("games_pipeline.x"), "build stg_games"):
        pass

    start, done = output.getvalue().splitlines()
    assert "> build stg_games" in start
    assert "+ build stg_games" in done
    assert done.rstrip().endswith("s")  # the duration


def test_a_failed_step_is_marked_and_the_error_is_raised_again(output):
    with (
        pytest.raises(RuntimeError),
        step(logging.getLogger("games_pipeline.x"), "load"),
    ):
        raise RuntimeError("boom")

    assert "x load  failed" in output.getvalue().splitlines()[-1]


def test_warnings_and_errors_have_their_own_marks(output):
    log = logging.getLogger("games_pipeline.x")
    log.warning("kept the rejected build")
    log.error("check failed")

    warning, error = output.getvalue().splitlines()
    assert "! kept the rejected build" in warning
    assert "x check failed" in error


def test_colour_is_only_added_when_asked_for():
    stream = io.StringIO()
    root = logging.getLogger()
    before = list(root.handlers), root.level
    try:
        configure_logging(stream=stream, color=True)
        logging.getLogger("games_pipeline.x").error("check failed")
        coloured = stream.getvalue()
        stream.truncate(0)
        stream.seek(0)
        configure_logging(stream=stream, color=False)
        logging.getLogger("games_pipeline.x").error("check failed")
        plain = stream.getvalue()
    finally:
        root.handlers[:], root.level = before

    assert "\x1b[" in coloured
    assert "\x1b[" not in plain


def test_configuring_twice_does_not_print_every_line_twice(output):
    configure_logging(stream=output, color=False)
    configure_logging(stream=output, color=False)

    logging.getLogger("games_pipeline.x").info("once")

    assert output.getvalue().count("once") == 1
