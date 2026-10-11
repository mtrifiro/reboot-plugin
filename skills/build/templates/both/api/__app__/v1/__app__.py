"""The __Title__ API.

The sample `Counter` type is a placeholder: replace it with the
application's own types, keeping `User` as the front door for both the
MCP UI and the web app.
"""

from reboot.api import (
    API,
    UI,
    Exclusive,
    Field,
    Methods,
    Model,
    Reader,
    Tool,
    Transaction,
    Type,
    Writer,
)

# -- User models. --


class UserState(Model):
    counter_ids: list[str] = Field(
        tag=1,
        default_factory=list,
        description="The IDs of the counters this user created, oldest first.",
    )


class CreateCounterResponse(Model):
    counter_id: str = Field(
        tag=1,
        default="",
        description="The ID of the new counter, to pass to later calls.",
    )


class ListCountersResponse(Model):
    counter_ids: list[str] = Field(
        tag=1,
        default_factory=list,
        description="The IDs of the user's counters, oldest first.",
    )


# -- Counter models. --


class CounterState(Model):
    value: int = Field(
        tag=1,
        default=0,
        description="The counter's current count. It starts at zero.",
    )


class GetResponse(Model):
    value: int = Field(
        tag=1,
        default=0,
        description="The counter's count when it was read.",
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
        description="A person who has signed in. Everything they "
        "create in the app is reached from here.",
        methods=Methods(
            create_counter=Transaction(
                mode=Exclusive(),
                request=None,
                response=CreateCounterResponse,
                description="Create a new counter and return its ID. "
                "The ID is not meant for people. Pass it to later tool "
                "calls instead of showing it to the user.",
                mcp=Tool(),
            ),
            list_counters=Reader(
                request=None,
                response=ListCountersResponse,
                description="List the IDs of the user's counters, "
                "oldest first.",
                mcp=Tool(),
            ),
        ),
    ),
    Counter=Type(
        state=CounterState,
        description="One counter a user created.",
        methods=Methods(
            show=UI(
                request=None,
                path="frontend/mcp/clicker",
                title="Counter",
                description="Show the counter with a button to "
                "increment it.",
            ),
            create=Writer(
                request=None,
                response=None,
                factory=True,
                description="Create the counter at zero.",
                mcp=None,
            ),
            get=Reader(
                request=None,
                response=GetResponse,
                description="Get the counter's current value.",
                mcp=Tool(),
            ),
            increment=Writer(
                request=IncrementRequest,
                response=None,
                description="Add `amount` to the counter.",
                mcp=Tool(),
            ),
        ),
    ),
)
