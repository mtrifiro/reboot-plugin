"""Shared test setup: the last run's results (last_run.py), and how far
a run is, for the Reboot band (run_progress.py)."""

# The last run's results, for the pull request and the release record
# (last_run.py).
from last_run import (  # noqa: F401
    pytest_sessionstart,
    pytest_terminal_summary,
    pytest_unconfigure,
)

from run_progress import (  # noqa: F401
    pytest_collection_finish,
    pytest_runtest_logreport,
    pytest_runtest_logstart,
    pytest_sessionfinish,
)

