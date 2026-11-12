"""Logging for the pipeline: one setup call for the commands, one helper for timed steps.

Every module logs through `logging.getLogger(__name__)`. Nothing is shown until a command
calls `configure_logging`, so tests and imports stay quiet. Progress goes to stderr, and
the summary table stays on stdout. Sign-in settings are never logged.
"""

import logging
import sys
import time
from contextlib import contextmanager

FORMAT = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"


def configure_logging(verbose=False):
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format=FORMAT,
        datefmt="%H:%M:%S",
        stream=sys.stderr,
    )
    # the connector is chatty at INFO: keep its logs for --verbose
    logging.getLogger("snowflake").setLevel(
        logging.DEBUG if verbose else logging.WARNING
    )


@contextmanager
def step(logger, message):
    """Log when a step starts and how long it took. A failure is logged and re-raised."""
    logger.info("%s ...", message)
    started = time.perf_counter()
    try:
        yield
    except Exception:
        logger.error("%s failed after %.1fs", message, time.perf_counter() - started)
        raise
    logger.info("%s done in %.1fs", message, time.perf_counter() - started)
