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
    count: int = Field(tag=1, default=0)


class GetResponse(Model):
    value: int = Field(tag=1, default=0)


class IncrementRequest(Model):
    amount: int = Field(tag=1, default=0)


api = API(
    User=Type(
        state=UserState,
        description="The signed-in user and their own state.",
        methods=Methods(
            get=Reader(
                request=None,
                response=GetResponse,
                description="Get the user's count.",
                # Every method states `mcp=`; a web app exposes no MCP
                # tools, so it is always `None`.
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
