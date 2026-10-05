from __app__.v1.__app___rbt import Counter, User
from reboot.aio.auth.authorizers import (
    allow_if,
    has_verified_token,
    is_app_internal,
)
from reboot.aio.contexts import (
    ReaderContext,
    TransactionContext,
    WriterContext,
)


class UserServicer(User.Servicer):
    # No `authorizer()`: the `User` default (`state_id_is_user_id` or
    # `is_app_internal`) is production-worthy.

    async def create_counter(
        self,
        context: TransactionContext,
    ) -> User.CreateCounterResponse:
        counter, _ = await Counter.create(context)
        return User.CreateCounterResponse(counter_id=counter.state_id)


class CounterServicer(Counter.Servicer):

    def authorizer(self):
        # Any signed-in user, plus app-internal calls (the `User`
        # transaction that creates the counter). Tighten this to the
        # app's real ownership rule.
        return allow_if(any=[has_verified_token, is_app_internal])

    async def create(self, context: WriterContext) -> None:
        # State starts at its zero defaults; nothing to do.
        pass

    async def get(self, context: ReaderContext) -> Counter.GetResponse:
        return Counter.GetResponse(value=self.state.value)

    async def increment(
        self,
        context: WriterContext,
        request: Counter.IncrementRequest,
    ) -> None:
        self.state.value += request.amount
