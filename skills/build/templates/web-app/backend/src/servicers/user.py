from __app__.v1.__app___rbt import User
from reboot.aio.contexts import ReaderContext, WriterContext


class UserServicer(User.Servicer):
    # No `authorizer()`: the `User` default (`state_id_is_user_id` or
    # `is_app_internal`) lets each signed-in user reach only their own
    # `User`. Every other servicer writes its rules from day one
    # (`python/references/servicer-authorizer.md`).

    async def get(self, context: ReaderContext) -> User.GetResponse:
        return User.GetResponse(value=self.state.count)

    async def increment(
        self,
        context: WriterContext,
        request: User.IncrementRequest,
    ) -> None:
        self.state.count += request.amount
