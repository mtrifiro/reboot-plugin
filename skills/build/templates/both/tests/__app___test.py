"""The __Title__ tests: the Gherkin scenarios in the `.feature` files
beside this module, run against the application below."""

import pytest
from reboot.aio.applications import Application
from reboot.aio.auth.oauth import OAuth
from reboot.aio.auth.oauth_providers import (
    Development,
    OAuthProviderByEnvironment,
)
from reboot.bdd import scenarios
from servicers.registry import SERVICERS, libraries


@pytest.fixture
def application() -> Application:
    development = Development()
    return Application(
        servicers=SERVICERS,
        libraries=libraries(),
        # The harness is neither `rbt dev run` nor `rbt serve`, so
        # name the Development picker for both, and list the allowed
        # origins explicitly (none: these scenarios open no browser).
        oauth=OAuth(
            provider=OAuthProviderByEnvironment(
                dev=development,
                prod=development,
            ),
            allowed_origins=[],
        ),
    )


scenarios('counting.feature')
