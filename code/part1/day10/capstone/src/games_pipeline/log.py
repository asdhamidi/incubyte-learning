"""Logging for the pipeline: one setup call for the commands, one helper for timed steps.

Every module logs through `logging.getLogger(__name__)`. Nothing is shown until a command
calls `configure_logging`, so tests and imports stay quiet. Progress goes to stderr, and
the result tables stay on stdout. Sign-in settings are never logged.

A line reads like this, with the mark showing what kind of line it is:

    12:01:03  > load games/games.csv into raw_games        a step starts
    12:01:15  + load games/games.csv into raw_games  12.4s  the step is done, with its time
    12:01:15    raw_games now holds 20058 rows               a plain note
    12:01:15  ! rejected build kept in stg_games_rejected    a warning
    12:01:15  x data quality check failed                    an error
"""

import logging
import os
import sys
import time
from contextlib import contextmanager

MARKS = {"start": ">", "done": "+"}
DIM, GREEN, YELLOW, RED, RESET = (
    "\x1b[2m",
    "\x1b[32m",
    "\x1b[33m",
    "\x1b[31m",
    "\x1b[0m",
)


class PrettyFormatter(logging.Formatter):
    """Time, a one-character mark and the message. The module name only with `verbose`."""

    def __init__(self, color=False, verbose=False):
        super().__init__()
        self.color = color
        self.verbose = verbose

    def format(self, record):
        kind = getattr(record, "kind", None)
        if kind in MARKS:
            mark, style = MARKS[kind], DIM if kind == "start" else GREEN
        elif record.levelno >= logging.ERROR:
            mark, style = "x", RED
        elif record.levelno >= logging.WARNING:
            mark, style = "!", YELLOW
        else:
            mark, style = " ", ""

        clock = time.strftime("%H:%M:%S", time.localtime(record.created))
        name = f" {record.name}:" if self.verbose else ""
        line = f"{clock}  {mark}{name} {record.getMessage()}"
        if record.exc_info:
            line += "\n" + self.formatException(record.exc_info)
        if self.color and style:
            line = f"{style}{line}{RESET}"
        return line


class _LiveStderrHandler(logging.StreamHandler):
    """Writes to whatever sys.stderr is at the moment of each line."""

    def __init__(self):
        logging.Handler.__init__(self)

    @property
    def stream(self):
        return sys.stderr

    @stream.setter
    def stream(self, _value):
        pass


def _wants_color(stream):
    return (
        hasattr(stream, "isatty")
        and stream.isatty()
        and "NO_COLOR" not in os.environ
        and os.environ.get("TERM") != "dumb"
    )


def configure_logging(verbose=False, stream=None, color=None):
    """Show the pipeline's progress. Calling it again replaces the earlier setup."""
    if color is None:
        color = _wants_color(stream or sys.stderr)
    if color and os.name == "nt":
        os.system("")  # switches on colour codes in the Windows console

    handler = _LiveStderrHandler() if stream is None else logging.StreamHandler(stream)
    handler.setFormatter(PrettyFormatter(color=color, verbose=verbose))
    handler._games_pipeline = True

    root = logging.getLogger()
    for old in [h for h in root.handlers if getattr(h, "_games_pipeline", False)]:
        root.removeHandler(old)
    root.addHandler(handler)
    root.setLevel(logging.DEBUG if verbose else logging.INFO)
    # the connector is chatty at INFO: keep its logs for --verbose
    logging.getLogger("snowflake").setLevel(
        logging.DEBUG if verbose else logging.WARNING
    )


@contextmanager
def step(logger, message):
    """Show when a step starts and how long it took. A failure is shown and raised again."""
    logger.info(message, extra={"kind": "start"})
    started = time.perf_counter()
    try:
        yield
    except Exception:
        elapsed = time.perf_counter() - started
        logger.error("%s  failed after %.1fs", message, elapsed)
        raise
    elapsed = time.perf_counter() - started
    logger.info("%s  %.1fs", message, elapsed, extra={"kind": "done"})
