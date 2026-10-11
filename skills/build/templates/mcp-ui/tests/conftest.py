"""Shared test setup: the last run's results (last_run.py), and how far
a run is, for the Reboot band (run_progress.py)."""

# The last run's results, for the pull request and the release record
# (last_run.py).
from last_run import (  # noqa: F401
    pytest_sessionstart,
    pytest_terminal_summary,
    pytest_unconfigure,
)

# Harness settings for a developer's machine: servers on loopback, a
# placeholder model key (harness_hygiene.py).
import harness_hygiene  # noqa: F401

# A Rule with no Scenario, and step shapes reboot.bdd reads as
# something else, named before the scenario runs (feature_lint.py).
from feature_lint import (  # noqa: F401
    pytest_collection_modifyitems,
    pytest_runtest_setup,
)

from run_progress import (  # noqa: F401
    pytest_collection_finish,
    pytest_runtest_logreport,
    pytest_runtest_logstart,
    pytest_sessionfinish,
)

