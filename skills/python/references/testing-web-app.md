---
title: Drive the Web App from Scenarios
impact: MEDIUM
impactDescription: A user-facing flow that is only tested at the backend leaves the page, the session cookie, and CORS untested; a page without accessible markup cannot be driven at all
tags: testing, bdd, web-app, playwright, frontend, vite, aria, accessible-name, recordings, sign-in
summary: "Pages need accessible markup (labels, named buttons) to be driven; the `frontend` fixture, web steps, clicked-through sign-in, recordings."
step: tests
applies: [web-app]
always: false
verified: 1.6.0
docs: ""
---

# Drive the Web App from Scenarios

## When you are here

A scenario opens the web frontend in a real browser (Playwright)
against the backend its backend steps call. Backend steps and feature
shape: [`testing-features.md`](testing-features.md). Reference:
[`reboot-bank-pydantic`](https://github.com/reboot-dev/reboot-bank-pydantic)'s
`tests/web_test.py`, `opening_accounts.feature`, `transfers.feature`,
`sign_in.feature`.

## Do this

Web app steps find things as a person does (a button by its text, a
field by its label, a table by its caption), never by CSS selector. A
page they can't drive has an accessibility bug: fix the markup, not the
scenario. Backend and web steps mix:

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
dev = ["reboot[dev]==<version>", "playwright>=1.55.0", "pytest-playwright>=0.7.1", ...]
```

```sh
uv sync
uv run playwright install chromium
cd web && npm install   # the web app's own dependencies (`frontend` in a dual-frontend app)
```

With both present, the `reboot` pytest plugin registers the web app
steps and records browser scenarios.

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
from servicers.registry import SERVICERS, libraries
from typing import Iterator


@pytest.fixture
def frontend() -> Iterator[Frontend]:
    # `web/` holds the SPA (`frontend/` in a dual-frontend app).
    with vite(directory='web') as frontend:
        yield frontend


@pytest.fixture
def application(frontend: Frontend) -> Application:
    assert frontend.origin is not None
    development = Development()
    return Application(
        servicers=SERVICERS,
        libraries=libraries(),
        # The harness is neither `rbt dev run` nor `rbt serve`.
        oauth=OAuth(
            provider=OAuthProviderByEnvironment(
                dev=development,
                prod=development,
            ),
            # The only origin Envoy lets read `/whoami` cross-origin.
            allowed_origins=[frontend.origin],
        ),
    )


scenarios('opening_accounts.feature', 'transfers.feature', 'sign_in.feature')
```

The app is served from its own origin (Vite on `localhost`) and calls
the backend cross-origin at `127.0.0.1`, exercising the session cookie,
the `whoami` probe and Envoy's CORS allow-list as production does. To
serve the web app another way, define `frontend` with your own
`Frontend` subclass; `in the web app` always means this fixture.

### The steps

Every step names a declared user. **Each user gets their own browser.**

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
- `eventually sees` takes `within`; `sees` takes none. A change shown
  after a reactive read is always `eventually`.
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

  Right-click is testable only if the frontend calls `preventDefault()`
  and renders its own `role="menu"`; HTML5 drag-and-drop often defeats
  `drag_to()`, so use `mouse.down()` / `move()` / `up()`.

### Look steps (template `tests/conftest.py`)

The web-app template ships five `Then` steps that fail a page breaking
the floor of `web-app/references/ui-design.md`. One scenario per page,
after it has loaded:

```gherkin
Then "alice" sees the web app fit a phone screen
And "alice" sees no loading text in the web app
And "alice" sees the web app use its own fonts
And "alice" sees the web app work in light and dark
And "alice" sees no clipped labels in the web app
```

Phone fit: no horizontal page scroll at 375 px. Loading text:
"Loading…" or "Loading...". Own fonts: the body's font isn't the
browser's default serif, and a named web font actually loaded (a system
stack passes). Light and dark: the `Switch to … mode` toggle, required
in a first build, changes the page background. Clipped labels: no short
label (stat tile, group band, header, pill, tab, button) is cut off.

These steps are a floor; the screenshot review (build Step 5) is where
the design is judged.

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

The Development picker lists accounts as links named by identity; a
custom provider's page uses the same generic steps. `is signed in`
waits for the browser to return to the app and asks the backend who
the session is; then `as "ben",` calls as that user (`with their user
id saved as` is optional). `is signed out` reverts to calling with no
token. Scenarios not about sign-in use `is an authenticated user`;
their browsers arrive signed in.

### Accessible markup the steps need

The steps find elements as a person does: a field by its paired label,
a button, link, tab or menu item by its text (or `aria-label` if
icon-only), a table, list or region by its caption or labeled heading, a
select by its label and its options' text, a value a scenario reads back
by `data-testid` on the element whose text is exactly that value (the
only place a test id belongs), and text that changes on a backend event
as visible text. The markup, with an example:
[`web-app/references/react-client.md`](../../web-app/references/react-client.md),
"Accessible markup". Build pages that way from the start; screen readers
need the same.

### Recordings and running

Each browser scenario records a video per user and a screenshot after
the opening step and each assertion (asserted element outlined):

```
tests/opening_accounts.recordings/
  opening-a-first-account-in-the-web-app/
    3f9c2a1b7d4e6f80/
      alice.webm
      2.png
      5.png
```

The digest directory hashes the scenario (name, background, steps,
examples); a run keeps only the current one, and an outline's examples
overwrite each other. `*.recordings/` goes in `.gitignore`; the
dashboard's Features page shows the last run's, or "not recorded yet".
`--recording-slowmo` (ms after each browser operation, default 500) and
`--recording-dwell` (ms an assertion stays on screen, default 1000)
pace only the browser; `0` disables either.

```sh
uv run pytest tests/web_test.py
uv run pytest tests/web_test.py -k "first account"
uv run pytest tests/web_test.py --recording-slowmo=0 --recording-dwell=0
```

CI without a browser or `node_modules` passes
`--ignore=tests/web_test.py` (as the bank's `.tests/test.sh` does).

## Never

- **A CSS selector or a test id on a button** — it means the button
  has no name; fix the markup.
- **A second `opens the web app` to test a reload** — it is a fresh
  profile with empty storage (no reload step exists); it means only
  "the same user on another machine".
- **A saved value in an `opens the web app at` path** — taken
  literally, `"/l/<lead id>"` loads a nonexistent id. Reach the page by
  clicking.
- **`saves the text of ...` after `Then`** — it is a `When`; under
  `Then` / `And` it fails "Step definition is not found".
- **`sees "55"` when the text appears twice** — a Playwright
  strict-mode violation. Save it via `data-testid`, or scope with
  `in the "..." table`.
- **`` fills ... with `Alice` ``** — the value is JSON; write
  `` `"Alice"` ``.
- **Quoted web text containing ` has ` or ` with `** ("Bad state has
  real consequences") — a catch-all step swallows it and fails "Almost:
  each clause goes in backticks". Rename the label.
- **`scope="module"` on the `frontend` fixture** — the second scenario
  fails `already serving`.

## Limits

- **One Vite boot per browser scenario is intrinsic**: Vite gets the
  backend URL at spawn and each scenario's backend has a fresh port
  (reboot-crm, 1.6.0).
- **Only a plain left click** is built in; everything else is a custom
  step (above).
- **A user who opens the app twice leaves a stray video**
  `page@<guid>.webm` (shown on the dashboard as a second video) holding
  the first browser, sign-in included (reboot-crm, 1.6.0).
- **A browser-only preference** (theme in `localStorage`) can't be
  asserted, since a reopen is a new profile.

## Scales as

- A browser scenario cost about 11.6 s vs about 1.6 s for a backend
  one; 11% of a 482-scenario suite took 47% of wall clock (reboot-crm, 1.6.0).

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `Almost: each clause goes in backticks` | Web text containing ` has ` / ` with ` hit the catch-all | Change the label |
| `"alice" has not opened the web app;` | A web step before `opens the web app` | Open it first |
| `AssertionError: already serving` | `frontend` fixture shared across scenarios | Keep it function-scoped |
| Playwright timeout with a `get_by_label` call log | The label's text differs from what the step says (often a hidden glyph) | Match the full label text, or drop the glyph from the label |

## See also

- [`testing-features.md`](testing-features.md) — backend steps, saved values
- [`../../web-app/SKILL.md`](../../web-app/SKILL.md) — building the page
- [`../../dashboard/SKILL.md`](../../dashboard/SKILL.md) — recordings on the Features page
