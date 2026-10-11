from __app__.v1.__app___rbt import Counter, User
from reboot.aio.contexts import TransactionContext


class UserServicer(User.Servicer):
    # No `authorizer()`: the `User` default (`state_id_is_user_id` or
    # `is_app_internal`) is production-worthy.

    async def create_counter(
        self,
        context: TransactionContext,
    ) -> User.CreateCounterResponse:
        counter, _ = await Counter.create(context)
        return User.CreateCounterResponse(counter_id=counter.state_id)
