---
title: React App.tsx — Generated Hooks and Component Patterns
impact: HIGH
impactDescription: The no-id `use<Type>()` hook resolves the actor from the MCP tool-call target but returns `{ <type>, isLoading }`, not the handle; reader and mutation calls go on the handle once it exists. Import from `@api/<pkg>/v1/<name>_rbt_react`. Many actors render through one composing reader.
tags: react, app-tsx, hooks, useType, css-module, snake-camel, import-path, default-id, composing-reader, pagination, ordered-map, multi-actor
summary: "No-id `use<Type>()` returns `{ <type>, isLoading }`: render a child once the handle exists; `_rbt_react` imports; composing readers."
step: frontend
applies: [mcp-ui]
always: false
verified: 1.6.0
docs: ""
---

# React App.tsx — Generated Hooks and Component Patterns

## When you are here

Writing `frontend/mcp/<ui-name>/App.tsx`, the component for one `UI()`
method: where the hook's actor ID comes from, the import path, and
rendering many actors through one subscription. The client contract
shared with web apps (`use<Type>()` overloads, `Use<Type>Api`, reader
fields, `{ response, aborted }` mutations, camelCase, Zod types) is
[`react-generated-client.md`](../../python/references/react-generated-client.md);
client-side state on top of the hooks is
[`patterns-react-state.md`](../../python/references/patterns-react-state.md).

## Do this

### Imports

```tsx
import {
  type DashboardConfig,
  type UseCounterApi,
  useCounter,
} from "@api/<pkg>/v1/<name>_rbt_react";
```

`<pkg>`/`<name>` are the API file's package and module
(`api/<pkg>/v1/<name>.py`); the `@api/*` alias is in the scaffolded
`vite.config.ts` ([`react-scaffolding.md`](react-scaffolding.md)).

### Resolve the actor, then render a child with the handle

For a `UI()` on an application `Type` (`Counter.show_clicker=UI(...)`),
call `use<Type>()` with **no `id`**: it resolves the ID from the tool
call's target and returns `{ <typeLowerCamel>, isLoading }`, the handle
`undefined` until resolved. Readers and mutations are hooks on the handle,
so put them in a child rendered once the handle exists:

```tsx
import { useState, type FC } from "react";
import {
  type UseCounterApi,
  useCounter,
} from "@api/mcp_ui_counter/v1/counter_rbt_react";
import css from "./App.module.css";

export const ClickerApp: FC = () => {
  // No `id`: resolved from the tool-call target.
  const { counter, isLoading } = useCounter();
  if (counter === undefined) {
    return (
      <div className={css.loading}>
        {isLoading ? "loading..." : "no counter"}
      </div>
    );
  }
  return <Clicker counter={counter} />;
};

const Clicker: FC<{ counter: UseCounterApi }> = ({ counter }) => {
  const [isPending, setIsPending] = useState(false);
  const { response, isLoading } = counter.useGet();

  const change = async (amount: number) => {
    setIsPending(true);
    try {
      // Resolves to `{ response, aborted }`; it never throws.
      if (amount > 0) {
        await counter.increment({ amount });
      } else {
        await counter.decrement({ amount: -amount });
      }
    } finally {
      setIsPending(false);
    }
  };

  if (isLoading && response === undefined) {
    return <div className={css.loading}>loading...</div>;
  }

  return (
    <div className={css.container}>
      <button onClick={() => change(-1)} disabled={isPending}
        className={css.buttonDecrement}>−</button>
      <div className={`${css.counter} ${isPending ? css.pending : ""}`}>
        {response?.value ?? 0}
      </div>
      <button onClick={() => change(1)} disabled={isPending}
        className={css.buttonIncrement}>+</button>
    </div>
  );
};
```

`App.module.css` sits beside it and themes through the scaffolded
`index.css` variables (`var(--color-bg)`, `var(--color-text)`,
`var(--color-pink)`, `var(--font-mono)`); copy the template's
`build/templates/mcp-ui/frontend/mcp/clicker/App.module.css` and add the
classes the component uses.

### Other actors: pass an explicit `id`

For a UI on `User`, or a component talking to an entity other than the
tool-call target, pass `{ id }`; that overload returns the handle
directly:

```tsx
const relatedPerson = usePerson({ id: relationship.otherPersonId });
```

`useMcpToolData()` from `@reboot-dev/reboot-react` returns the raw tool
input, for following a chain to another entity.

### Many actors: one composing reader

For a correctly decomposed collection — each item its own `Type`, indexed
by an `OrderedMap` on the parent (Shape C in
[`state-collections.md`](../../python/references/state-collections.md)) —
keep it decomposed and give the front-door type a `mcp=None` `Reader` that
pages the index and reads each item: one UI subscription, fan-out
server-side
([`patterns-cross-actor-reads.md`](../../python/references/patterns-cross-actor-reads.md)).

```python
async def dashboard(
    self,
    context: ReaderContext,
    request: User.DashboardRequest,
) -> User.DashboardResponse:
    # `items_index_id`: a parent state field allocated once in its
    # constructor — never synthesized from the state ID.
    page = await OrderedMap.ref(self.state.items_index_id).range(
        context, start_key=request.cursor or None, limit=32,
    )
    items = []
    for entry in page.entries:
        item_id = entry.bytes.decode()
        view = await Item.ref(item_id).get(context)
        items.append(
            User.DashboardItem(
                item_id=item_id, title=view.title, status=view.status,
            )
        )
    return User.DashboardResponse(
        items=items,
        # `start_key` is inclusive: step past the last key.
        next_cursor=(page.entries[-1].key + "\x00" if page.entries else ""),
    )
```

```tsx
import { useState, type FC } from "react";
import { type UseUserApi, useUser } from "@api/<pkg>/v1/<name>_rbt_react";

export const Dashboard: FC = () => {
  const { user, isLoading } = useUser();
  if (user === undefined) {
    return <div>{isLoading ? "loading..." : "not signed in"}</div>;
  }
  return <DashboardPage user={user} />;
};

const DashboardPage: FC<{ user: UseUserApi }> = ({ user }) => {
  const [cursor, setCursor] = useState("");
  // One subscription; every item actor it read re-pushes it.
  const { response } = user.useDashboard({ cursor });
  const items = response?.items ?? [];
  const nextCursor = response?.nextCursor ?? "";
  return (
    <div>
      {items.map((item) => (
        <div key={item.itemId}>{item.title} — {item.status}</div>
      ))}
      {nextCursor && (
        <button onClick={() => setCursor(nextCursor)}>Load more</button>
      )}
    </div>
  );
};
```

`setCursor` replaces the page; for an ever-growing list, accumulate
`response.items` into component state.

## Never

- `const counter = useCounter(); counter.useGet()` — the no-id overload
  returns `{ counter, isLoading }` (since 1.3.0), so `counter.useGet` is
  not a function. Destructure, then render a child taking
  `UseCounterApi`.
- `counter?.useGet()` behind a condition in the same component — breaks
  the rules of hooks. Split the component.
- `show_person=UI(request=...)` on `User` plus `usePerson({ id: personId })`
  from a prop — put the UI on `Person` and use the no-id hook
  ([`api-method-types.md`](api-method-types.md)).
- Flattening a decomposed collection back into `list[Item]` on one actor
  to regain a single subscription — use the composing reader.
- An unguarded `useMcpApp().sendMessage(...)` — `useMcpApp()` can return
  `null` on early renders; use `app?.`.
- Importing hooks from anything but `<name>_rbt_react` — they are emitted
  only there.

## Limits

- ID resolution order (1.6.0 generated hook): explicit `{ id }`, then a
  `?<pkg>.v1.<Type>.id=<id>` URL parameter (dev), then the default-ID map
  filled from the tool-call target, keyed by the state's full name
  (`<pkg>.v1.<Type>`). With none, the handle is `undefined` and
  `isLoading` turns `false`.
- The provider renders the UI immediately without waiting for the tool
  input, so first renders see `isLoading: true`.

## Scales as

- One composing reader replaces N per-item subscriptions; costs and the
  ~15-per-page threshold are in
  [`patterns-react-state.md`](../../python/references/patterns-react-state.md).

## Errors you will see

`state ID must have a length of at least 1`: see `react-generated-client.md`.

## See also

- [`react-generated-client.md`](../../python/references/react-generated-client.md) — hook and mutation shapes
- [`api-method-types.md`](api-method-types.md) — where each `UI()` lives
- [`patterns-react-state.md`](../../python/references/patterns-react-state.md) — client state, subscription budget
