import asyncio
import logging

from reboot.aio.applications import Application
from reboot.aio.auth.oauth import OAuth
from reboot.aio.auth.oauth_providers import (
    Development,
    OAuthProviderByEnvironment,
)
from servicers.__app__ import UserServicer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


async def main() -> None:
    application = Application(
        title="__Title__",
        description="Replace with one sentence on what the app does.",
        servicers=[UserServicer],
        oauth=OAuth(
            # `prod=None` refuses to start under `rbt serve` until a
            # real provider is chosen.
            provider=OAuthProviderByEnvironment(
                dev=Development(),
                prod=None,
            ),
            # Cross-origin browser origins allowed to sign in. `[]` is
            # same-origin only; `rbt dev run` adds `http://localhost(:*)`
            # by itself. Before deploying, list the SPA's production
            # origin (e.g. "https://app.example.com"); see the `deploy`
            # skill. Leaving it out entirely fails at startup in prod.
            allowed_origins=[],
        ),
    )
    await application.run()


if __name__ == "__main__":
    asyncio.run(main())
