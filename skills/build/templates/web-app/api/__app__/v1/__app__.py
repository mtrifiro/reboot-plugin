"""The __Title__ API.

The sample `count` on `User` is a placeholder: replace it with the
application's own state and types.
"""

from reboot.api import (
    API,
    Field,
    Methods,
    Model,
    Reader,
    Type,
    Writer,
)


class UserState(Model):
    count: int = Field(
        tag=1,
        default=0,
        description="How many times this user has counted. It starts at zero.",
    )


class GetResponse(Model):
    value: int = Field(
        tag=1,
        default=0,
        description="The user's count when it was read.",
    )


class IncrementRequest(Model):
    amount: int = Field(
        tag=1,
        default=0,
        description="How much to add to the count. A negative amount "
        "lowers it.",
    )


api = API(
    User=Type(
        state=UserState,
        description="A person who has signed in, and the count that "
        "belongs to them.",
        methods=Methods(
            get=Reader(
                request=None,
                response=GetResponse,
                description="Get the user's count.",
                # Every method states `mcp=`: `None` until an MCP UI is
                # added, then `Tool()` on what the AI calls. Changing it
                # is compatible; changing `description=` after a deploy
                # is not, so write it for the AI now.
                mcp=None,
            ),
            increment=Writer(
                request=IncrementRequest,
                response=None,
                description="Add `amount` to the user's count.",
                mcp=None,
            ),
        ),
    ),
)
