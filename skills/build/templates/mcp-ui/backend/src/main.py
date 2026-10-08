import asyncio
import logging

from example_prompts import example_prompts
from reboot.aio.applications import Application
from reboot.aio.auth.oauth import OAuth
from reboot.aio.auth.oauth_providers import (
    Development,
    OAuthProviderByEnvironment,
)
from servicers.registry import SERVICERS, libraries

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


async def main() -> None:
    application = Application(
        title="__Title__",
        description="Replace with one sentence on what the app does.",
        servicers=SERVICERS,
        libraries=libraries(),
        # `User` is auto-constructed for each signed-in user, which
        # requires `oauth=`. `prod=None` refuses to start under
        # `rbt serve` until a real provider is chosen.
        oauth=OAuth(
            provider=OAuthProviderByEnvironment(
                dev=Development(),
                prod=None,
            ),
            # MCP UIs are served from the backend's own origin, so no
            # cross-origin browser needs credentials. Leaving this out
            # entirely fails at startup in production.
            allowed_origins=[],
        ),
        example_prompts=example_prompts,
    )
    await application.run()


if __name__ == "__main__":
    asyncio.run(main())
