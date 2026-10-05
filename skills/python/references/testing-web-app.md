---
title: Drive the Web App from Scenarios
impact: MEDIUM
impactDescription: A user-facing flow that is only tested at the backend leaves the page, the session cookie, and CORS untested; a page without accessible markup cannot be driven at all
tags: testing, bdd, web-app, playwright, frontend, vite, aria, accessible-name, recordings, sign-in
summary: "The `frontend` fixture and web app steps, sign-in clicked through then bound, recordings, and the accessible markup (paired labels, named buttons, captioned tables) a page needs to be driven."
step: tests
applies: [web-app]
always: false
verified: 1.6.0
docs: ""
---

# Drive the Web App from Scenarios

## When you are here

A scenario needs to open the app's web frontend in a real browser
(Playwright) against the same backend its backend steps call. The
backend steps and the shape of a feature are
[`testing-features.md`](testing-features.md). The
[`reboot-bank-pydantic`](https://github.com/reboot-dev/reboot-bank-pydantic)
example's `tests/web_test.py` and its `opening_accounts.feature`,
`transfers.feature` and `sign_in.feature` are the reference.

## Do this

The web app steps find things the way a person does: a button by what
it says, a field by its label, a table by its caption. They never take
a CSS selector. A page they cannot find things on has an accessibility
bug, fixed in the markup, not the scenario. Backend and web steps mix:

```gherkin
Scenario: Opening a first account in the web app
  Given "alice" is an authenticated user
  When "alice" opens the web app
  Then "alice" sees "Signed in as alice" in the web app
  When "alice" fills "Initial Deposit ($)" in the web app with `1000`
  And "alice" clicks the "Open Account" button in the web app
  Then "alice" eventually sees "$1000" in the "Your Accounts" table in the web app within 10 seconds
  When "alice" saves the text of the "account-id" element in the web app as "account id"
  Then as "alice", `balance` on the `Account` for "<account id>" has `amount=1000.0`
```

### Install

```toml
[dependency-groups]
dev = [
    "reboot[dev]==<version>",
    "playwright>=1.55.0",
    "pytest-playwright>=0.7.1",
    ...
]
```

```sh
uv sync
uv run playwright install chromium
cd frontend && npm install   # the web app's own dependencies
```

With `playwright` and `pytest-playwright` present, the `reboot` pytest
plugin registers the web app steps and records every browser scenario.

### The `frontend` fixture and the application

```python
import pytest
from reboot.aio.applications import Application
from reboot.aio.auth.oauth import OAuth
from reboot.aio.auth.oauth_providers import (
    Development,
    OAuthProviderByEnvironment,
)
from reboot.bdd import scenarios
from reboot.bdd.frontend import Frontend
from reboot.bdd.vite import vite
from typing import Iterator


@pytest.fixture
def frontend() -> Iterator[Frontend]:
    with vite(directory='frontend') as frontend:
        yield frontend


@pytest.fixture
def application(frontend: Frontend) -> Application:
    # A web app calls the backend from its own origin.
    assert frontend.origin is not None
    development = Development()
    return Application(
        servicers=[...],
        # The harness is neither `rbt dev run` nor `rbt serve`, so
        # name the Development picker for both.
        oauth=OAuth(
            provider=OAuthProviderByEnvironment(
                dev=development,
                prod=development,
            ),
            # The app's origin is the only one Envoy lets read
            # `/whoami` cross-origin, as a deployment lists its host.
            allowed_origins=[frontend.origin],
        ),
    )


scenarios('opening_accounts.feature', 'transfers.feature', 'sign_in.feature')
```

The app is served from its own origin (Vite on `localhost`) and calls
the backend cross-origin at `127.0.0.1`, so the session cookie, the
`whoami` probe and Envoy's CORS allow-list are exercised as production
exercises them. A project that serves its web app another way defines
`frontend` against its own `Frontend` subclass; `in the web app`
always means this fixture.

### The steps

Every step names a user the scenario declared. **Each user gets a
browser of their own.**

| Step | What it does |
| --- | --- |
| `"alice" opens the web app` | Opens a **new** browser for alice at the app's origin (`at "/path"` for another page) |
| `"alice" clicks the "Open Account" button in the web app` | Plain left click on the element of that role and accessible name |
| `` "alice" fills "Amount ($)" in the web app with `250` `` | Fills the field with that label; the value is JSON: `` with `"Alice"` `` for text |
| `"alice" selects "<first account id>" in "From Account" in the web app` | Picks an option in the select with that label |
| `"alice" checks "Remember me" in the web app` / `unchecks` | Sets the checkbox with that label |
| `"alice" presses "Enter" in the web app` | Presses a key in the focused element (`Shift+Tab` works) |
| `"alice" sees "$1000" in the web app` | Asserts the text is visible now |
| `"alice" sees "$1000" in the "Your Accounts" table in the web app` | Asserts the text within that element |
| `"alice" eventually sees "$1000" in the web app within 10 seconds` | Waits for the text, at most that long |
| `"alice" does not see "<carol account id>" in the web app` | Asserts the text is absent |
| `"alice" sees the "Sign in" button in the web app is enabled` / `is disabled` | Asserts the element's state |
| `"alice" sees the web app at "/accounts"` | Asserts the page's path |
| `"alice" saves the text of the "account-id" element in the web app as "id"` | A **`When`**: reads an element by `data-testid` into a saved value |
| `"bob" is signed in to the web app with their user id saved as "bob id"` | Binds bob's browser session to bob (below) |
| `"bob" is signed out of the web app` | Waits for bob's session to end (below) |

- **Roles** are a closed list: `button`, `link`, `tab`, `checkbox`,
  `radio`, `menuitem`, `option`, `row`, `table`.
- **Two ways of naming**: `clicks` and `sees the ... button` match the
  accessible name exactly (an `aria-hidden` glyph inside is excluded);
  `fills`, `checks`, `selects` match the label's text exactly with
  `get_by_label` (the glyph is included).
- **Quoted text may say `<name>`** for a saved value, in every step
  except the path of `opens the web app at`.
- `eventually sees` takes `within`; `sees` takes none. A change the
  page shows after a reactive read is always `eventually`.
- **Gestures other than a left click** (double, right, modifier-click,
  hover, drag) are custom steps over the Playwright `Page`:

```python
from reboot.bdd import parsers, when
from reboot.bdd.web import WebApp


@when(parsers.parse(
    '"{user}" double-clicks the "{name}" {role} in the web app'
))
def _double_clicks(web_app: WebApp, user: str, name: str, role: str) -> None:
    web_app.page(user=user).get_by_role(role, name=name, exact=True).dblclick()
```

  A right-click is testable only if the frontend calls
  `preventDefault()` and renders its own `role="menu"`; HTML5
  drag-and-drop often defeats `drag_to()` and needs
  `mouse.down()` / `move()` / `up()`.

### Signing in is clicked through, then bound

```gherkin
Scenario: Signing in and out with the Development picker
  Given "ben" is an unauthenticated user
  When "ben" opens the web app
  And "ben" clicks the "Sign in" button in the web app
  And "ben" clicks the "Ben" link in the web app
  Then "ben" is signed in to the web app with their user id saved as "ben user id"
  When "ben" fills "Initial Deposit ($)" in the web app with `500`
  And "ben" clicks the "Open Account" button in the web app
  Then "ben" eventually sees "$500" in the "Your Accounts" table in the web app within 10 seconds
  And as "ben", `balances` on the `User` for "<ben user id>" eventually has `balances` of length `1` and `balances[0].balance=500.0` within 10 seconds
  When "ben" clicks the "Sign out" button in the web app
  Then "ben" is signed out of the web app
  And as "ben", `balances` on the `User` for "<ben user id>" aborts with `Unauthenticated`
```

The Development picker lists accounts as links named by identity. A
custom identity provider's page is driven with the same generic
steps; only the binding step is Reboot's. `is signed in` waits for the
browser to return to the app and asks the backend who the session is;
from then on `as "ben",` calls as that user (the `with their user id
saved as` part is optional). `is signed out` returns the user to
calling with no token. A scenario not about sign-in declares people
with `is an authenticated user`; their browsers arrive signed in.

### Accessible markup the steps need

- **A field's label is paired with it** (`<label htmlFor="amount">` +
  `<input id="amount">`, or the input inside the label). A placeholder
  or a nearby heading does not count.
- **A button, link, tab or menu item says what it does** in its text,
  or in `aria-label` when it is only an icon.
- **A table, list or region a step names has a caption or a labelled
  heading**: `<table aria-labelledby="your-accounts">` with
  `<h2 id="your-accounts">Your Accounts</h2>`, or a `<caption>`.
- **A select is a `<select>` with a paired label**, its `<option>`s
  saying the value a scenario picks.
- **A value a scenario reads back** (an id the app made up) carries
  `data-testid` on the element whose text is exactly that value. This
  is the only place a test id belongs.
- **Text that changes on a backend event** is rendered as visible
  text, not only an attribute or a canvas.

Build pages this way from the start; a screen reader needs the same.

### Recordings and running

Every browser scenario is recorded: a video per user and a screenshot
after the opening step and each assertion, the asserted element
outlined:

```
tests/opening_accounts.recordings/
  opening-a-first-account-in-the-web-app/
    3f9c2a1b7d4e6f80/
      alice.webm
      2.png
      5.png
```

The digest directory names what the scenario runs (name, background,
steps, examples); a run keeps only the current one, and an outline's
examples overwrite each other. `*.recordings/` goes in `.gitignore`;
the dashboard's Features page shows the last run's, or "not recorded
yet". `--recording-slowmo` (ms after each browser operation, default
500) and `--recording-dwell` (ms an assertion stays on screen, default
1000) pace only the browser; `0` turns either off.

```sh
uv run pytest tests/web_test.py
uv run pytest tests/web_test.py -k "first account"
uv run pytest tests/web_test.py --recording-slowmo=0 --recording-dwell=0
```

A CI run without a browser or `node_modules` passes
`--ignore=tests/web_test.py`, as the bank's `.tests/test.sh` does.

## Never

- **A CSS selector or a test id on a button** — a button with a test id
  is a button without a name; fix the markup.
- **A second `opens the web app` to test a reload** — it is a fresh
  browser profile with empty storage. There is no reload step; use it
  only to mean "the same user on another machine".
- **A saved value in an `opens the web app at` path** — the path is
  taken as written, so `"/l/<lead id>"` loads a page for an id that does
  not exist. Reach the page by clicking, as a person does.
- **`saves the text of ...` after `Then`** — it is a `When`; under
  `Then` / `And` it fails "Step definition is not found".
- **`sees "55"` when the text appears twice** — Playwright refuses
  it with a strict-mode violation. Give the value a `data-testid` and save it, or
  scope with `in the "..." table`.
- **`` fills ... with `Alice` ``** — the value is JSON; write
  `` `"Alice"` ``.
- **Quoted web text containing ` has ` or ` with `** (a label such as
  "Bad state has real consequences") — a catch-all step swallows it and
  fails "Almost: each clause goes in backticks". Rename the label.
- **`scope="module"` on the `frontend` fixture** — the second scenario
  fails `already serving`.

## Limits

- **One Vite boot per browser scenario is intrinsic**: the backend URL
  is passed to Vite at spawn and each scenario's backend gets a fresh
  port (reboot-crm, 1.6.0).
- **Only a plain left click** is built in; everything else is a custom
  step (above).
- **A user who opens the app twice leaves a stray video** named
  `page@<guid>.webm`, which the dashboard shows as a second video; it
  holds the first browser, sign-in included (reboot-crm, 1.6.0).
- **A browser-only preference** (theme in `localStorage`) has no
  reachable assertion, since a reopen is a new profile.

## Scales as

- A browser scenario cost about 11.6 s against about 1.6 s for a
  backend one; 11% of a 482-scenario suite took 47% of the wall clock
  (reboot-crm, 1.6.0).

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `Step definition is not found:` | A `When`-only step (`saves the text of`, `clicks`, `fills`) under `Then` | Put it under `When` |
| `Almost: each clause goes in backticks` | Web text containing ` has ` / ` with ` hit the catch-all | Change the label |
| `"alice" has not opened the web app;` | A web step before `opens the web app` | Open it first |
| `AssertionError: already serving` | `frontend` fixture shared across scenarios | Keep it function-scoped |
| Playwright timeout with a `get_by_label` call log | The label's text differs from what the step says (often a hidden glyph) | Match the full label text, or drop the glyph from the label |

## See also

- [`testing-features.md`](testing-features.md) — backend steps, saved values
- [`../../web-app/SKILL.md`](../../web-app/SKILL.md) — building the page
- [`../../dashboard/SKILL.md`](../../dashboard/SKILL.md) — recordings on the Features page
