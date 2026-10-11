---
title: A Staff Roster with Roles
impact: HIGH
impactDescription: Three builds of one brief invented three rosters; two let any sign-in with a listed address take its role, and one left the first admin to whoever signed in first in production
tags: auth, roles, roster, team, invitations, allowlist, first admin, email_verified, staff, manager
summary: "Roles live on one roster actor; invitations need a verified email; the first admin comes from an allowlist."
step: auth
applies: [mcp-ui, web-app, backend-only]
always: false
when: "staff sign in with roles (a manager, a host, a server; editors and readers)"
verified: 1.6.0
docs: ""
---

# A Staff Roster with Roles

## When you are here

The brief says staff sign in and what each may do depends on their
role. Predicates and per-method rules are
[`auth-custom-predicates.md`](auth-custom-predicates.md); how the
provider's claims reach the app is [`auth-claims.md`](auth-claims.md).
This file is the shape that goes on top: where roles live, how a
caller's role is asked, how people are invited before they arrive, and
who the first admin is. It is reboot-crm's `Team`, which three later
builds of a staffed app each reinvented, differently.

## Do this

### One roster owns every role

A singleton roster type (`Team`) holds the members and their roles, the
invitations, and the aliases that tie an invitation to the person who
arrived at it. No method on `User` writes a role, so nobody can promote
themselves; `User` keeps only what the provider delivered (`email`,
`email_verified`, `name`).

```python
class Member(Model):
    user_id: str = Field(tag=1, default="")
    role: str = Field(tag=2, default="")      # "manager" | "host" | "server"

class Invitation(Model):
    email: str = Field(tag=1, default="")     # lower-cased
    role: str = Field(tag=2, default="")

class OwnerAlias(Model):
    owner_id: str = Field(tag=1, default="")  # "invited:<email>"
    user_id: str = Field(tag=2, default="")

class TeamState(Model):
    members: list[Member] = Field(tag=1, default_factory=list)
    invitations: list[Invitation] = Field(tag=2, default_factory=list)
    aliases: list[OwnerAlias] = Field(tag=3, default_factory=list)
```

Two readers, named for who asks: `my_role` answers the caller (the UI
shows what they may do) and `role_of(user_id)` answers a predicate.
One app-internal writer, `register`, runs from `User.set_claims` on
every sign-in; `invite` and `set_role` are manager-only.

### Two gates: access, then role

**Access** ("may you get in") is an allowlist of verified addresses or
domains, checked on the caller's own `User`, where the address already
is, so it costs no extra read. **Role** ("what may you do") is asked of
the roster, only on the methods that need it.

```python
def is_on_the_team(*, context, state: Any = None, **kwargs) -> Authorizer.Decision:
    """On the caller's own User: the allowlist, read off the state."""
    if context.app_internal:
        return errors.Ok()
    if context.auth is None or not context.auth.user_id:
        return errors.Unauthenticated()
    if isinstance(state, UserState) and state.email_verified \
            and allowed(state.email):
        return errors.Ok()
    return errors.PermissionDenied()

async def is_manager(*, context, **kwargs) -> Authorizer.Decision:
    if context.app_internal:
        return errors.Ok()
    if context.auth is None or not context.auth.user_id:
        return errors.Unauthenticated()
    role = await Team.ref(TEAM_ID).role_of(context, user_id=context.auth.user_id)
    return errors.Ok() if role.role == "manager" else errors.PermissionDenied()

# On User: the door. On every other type: the team, then the role
# where a method needs one.
User.Authorizer(set_claims=allow_if(all=[is_app_internal]),
                _default=allow_if(all=[state_id_is_user_id, is_on_the_team]))
Check.Authorizer(void=allow_if(all=[is_manager]), _default=teammate())
```

A method a client or an MCP host calls that fans out to other actors
checks its own caller first: what it calls arrives app-internal and
passes every gate behind it.

### Invitations that keep their place

A manager invites by address. Records handed to the invitee before they
arrive are owned by `invited:<email>`. On arrival, `register` adopts the
invitation **only on the provider's word**: an unverified address is a
claim anybody can make.

```python
async def register(self, context: WriterContext, request: Team.RegisterRequest) -> None:
    email = request.email.strip().lower()
    invited = None
    if email and request.email_verified:
        invited = next((i for i in self.state.invitations if i.email == email), None)
    if invited is not None:
        role = invited.role
        self.state.invitations = [i for i in self.state.invitations if i.email != email]
        self.state.aliases.append(OwnerAlias(owner_id=f"invited:{email}", user_id=request.user_id))
    elif any(m.user_id == request.user_id for m in self.state.members):
        return
    else:
        role = DEFAULT_ROLE
    self.state.members.append(Member(user_id=request.user_id, role=role))
```

Nothing is rewritten: a reader that answers "mine" accepts both the
user id and its aliases. A removed member's alias goes with them.

### The first admin

Never "the first to sign in" in production. The deploy names the
starting admin (an `ADMIN_EMAILS` or allowlist variable, set with
`rbt cloud secret set`), `main.py` refuses to start when a real provider
is configured and no allowlist is set, and `initialize` repairs an empty
roster on every boot under a fresh alias (a bare call runs once ever,
[`lifecycle-initialize-hook.md`](lifecycle-initialize-hook.md)):

```python
if os.environ.get("GOOGLE_OAUTH_CLIENT_ID") and not allowlist_configured():
    raise SystemExit("GOOGLE_OAUTH_CLIENT_ID is set but no ALLOWED_EMAILS / "
                     "ALLOWED_EMAIL_DOMAINS; set one so sign-in is limited to the team.")
...
await Team.ref(TEAM_ID).idempotently(alias=f"repair at {uuid4()}").repair_admin(context)
```

Under `rbt dev run` and in the harness, with no allowlist, the first to
register is the manager; that is a development convenience, and the
refusal above is what keeps it out of production.

### The feature file that proves it

```gherkin
@wip
Feature: Staff sign in with roles
  Rule: The first to arrive on an empty roster is the manager
    Scenario: Opening day
      Given "ana" is an authenticated user with `email="ana@crudo.test"` and `email_verified=true`
      Then as "ana", `my_role` on the `Team` for "team" has `role="manager"`
  Rule: An invited host takes the invited role on arrival, on a verified address only
    Scenario: An invitation adopted
      Given "ana" is an authenticated user with `email="ana@crudo.test"` and `email_verified=true`
      And "ana" does an `invite` with `email="ben@crudo.test"` and `role="host"` on `Team` of "team"
      When "ben" is an authenticated user with `email="ben@crudo.test"` and `email_verified=true`
      Then as "ben", `my_role` on the `Team` for "team" has `role="host"`
    Scenario: An unverified address claims nothing
      Given "ana" is an authenticated user with `email="ana@crudo.test"` and `email_verified=true`
      And "ana" does an `invite` with `email="ben@crudo.test"` and `role="host"` on `Team` of "team"
      When "mallory" is an authenticated user with `email="ben@crudo.test"` and `email_verified=false`
      Then as "mallory", `my_role` on the `Team` for "team" has `role="server"`
  Rule: The last manager cannot be removed
    Scenario: Ana stays
      Given "ana" is an authenticated user with `email="ana@crudo.test"` and `email_verified=true`
      When "ana" attempts a `remove_member` with `user_id="ana"` on `Team` of "team"
      Then the attempt aborts with `LastManagerError`
```

The sign-in step with claims is a custom step (the built-in one mints a
token with no claims), over the harness's
`make_valid_oauth_access_token(user_id=..., claims={...})`
([`testing-harness.md`](testing-harness.md)); it runs the real
`set_claims` and `register`.

## Never

- Link a sign-in to a roster entry, an invitation or any email-keyed
  record unless `request.claims["email_verified"]` is true. Two builds
  keyed roles by `email` and never read the flag; with a provider that
  issues unverified addresses, anyone could take a listed address's
  role, and `Development()` (five fabricated, verified addresses) never
  shows it.
- A `role` field on `User` that a method on `User` writes. The roster
  owns roles; a predicate asks it.
- Key the roster by `Development()` user ids
  ([`auth-claims.md`](auth-claims.md) § Never); by `email`, with the
  check above, or by the sign-in id with invitations by verified email.
- "The first to sign in is the admin" in production, or an allowlist
  that may be empty with a real provider configured: with
  `has_verified_token` alone every account at the provider can read the
  app.
- A predicate on the roster type calling a reader on the roster: the
  actor waits on itself. Read the `state` argument.
- Asking the roster on every method of every type: put the access gate
  on the caller's own `User` and ask the roster only where a role
  decides.

## Limits

- `Development()` has five identities and delivers claims only with
  `claims=["email", "email_verified", "name"]`.
- The built-in `is an authenticated user` step mints a token with no
  claims; a scenario about roles needs the custom step above.
- A role asked of the roster is one reader call on a singleton per
  protected call, live subscriptions included; the access gate on `User`
  is free.

## Scales as

- reboot-crm: one roster read per admin-gated call, none per teammate
  call; the roster actor saw no contention at a dozen staff. A roster of
  thousands belongs in an `OrderedMap`
  ([`state-collections.md`](state-collections.md)).

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `aborted with 'Unauthenticated'` on a role-gated method called from another servicer or `initialize` | The predicate asked `context.auth` on an app-internal call | Return `Ok` for `context.app_internal` first |
| Every signed-in user is `PermissionDenied` on a fresh production deploy | No allowlist or starting admin named | Set `ALLOWED_EMAILS` / `ALLOWED_EMAIL_DOMAINS` (`rbt cloud secret set`); `main.py` should have refused to start |

## See also

- [`auth-custom-predicates.md`](auth-custom-predicates.md) — the predicates' shape and per-method rules
- [`auth-claims.md`](auth-claims.md) — requesting `email_verified`, `set_claims`
- [`testing-harness.md`](testing-harness.md) — a token with claims in a test
