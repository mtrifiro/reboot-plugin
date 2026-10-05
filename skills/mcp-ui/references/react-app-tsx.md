---
title: React App.tsx — Generated Hooks and Component Patterns
impact: HIGH
impactDescription: The no-id `use<Type>()` hook resolves the actor from the MCP tool-call target but returns `{ <type>, isLoading }`, not the handle; reader and mutation calls go on the handle once it exists. Import from `@api/<pkg>/v1/<name>_rbt_react`. Many actors render through one composing reader.
tags: react, app-tsx, hooks, useType, css-module, snake-camel, import-path, default-id, composing-reader, pagination, ordered-map, multi-actor
summary: "No-id `use<Type>()` returns `{ <type>, isLoading }` resolved from the tool-call target — render a child once the handle exists; import `@api/<pkg>/v1/<name>_rbt_react`; composing reader for many actors."
step: frontend
applies: [mcp-ui]
always: false
verified: 1.6.0
docs: ""
---

# React App.tsx — Generated Hooks and Component Patterns

## When you are here

You are writing `frontend/mcp/<ui-name>/App.tsx`, the React component
for one `UI()` method. This file covers what is specific to a UI inside
an MCP host: where the hook's actor ID comes from, the import path, the
Counter example, and rendering many actors through one subscription.
The generated client contract shared with web apps — the `use<Type>()`
overloads, `Use<Type>Api`, reader fields, `{ response, aborted }`
mutations, camelCase naming, Zod types — is in
[`react-generated-client.md`](../../python/references/react-generated-client.md);
where client-side state lives on top of those hooks is in
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

The path is `@api/<pkg>/v1/<name>_rbt_react` — `<pkg>` and `<name>` are
the API file's package and module (`api/<pkg>/v1/<name>.py`); the
`@api/*` alias comes from the scaffolded `vite.config.ts`
([`react-scaffolding.md`](react-scaffolding.md)).

### Resolve the actor, then render a child with the handle

For a `UI()` declared on an application `Type`
(`Counter.show_clicker=UI(...)`), call `use<Type>()` with **no `id`**.
It resolves the actor ID from the MCP tool call's target and returns
`{ <typeLowerCamel>, isLoading }`; the handle is `undefined` until the
ID resolves. Readers and mutations are hooks on the handle, so they live
in a child that only renders once the handle exists:

```tsx
import { useEffect, useRef, useState, type FC } from "react";
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
      <div className={css.container}>
        <div className={css.loading}>
          {isLoading ? "loading..." : "no counter"}
        </div>
      </div>
    );
  }
  return <Clicker counter={counter} />;
};

const Clicker: FC<{ counter: UseCounterApi }> = ({ counter }) => {
  const [isPending, setIsPending] = useState(false);
  const { response, isLoading } = counter.useGet();

  const prevValueRef = useRef<number | null>(null);
  const [trend, setTrend] = useState<"up" | "down" | "same" | null>(null);

  const value = response?.value ?? 0;

  useEffect(() => {
    if (response?.value !== undefined) {
      if (prevValueRef.current !== null) {
        if (response.value > prevValueRef.current) {
          setTrend("up");
        } else if (response.value < prevValueRef.current) {
          setTrend("down");
        } else {
          setTrend("same");
        }
      }
      prevValueRef.current = response.value;
    }
  }, [response?.value]);

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

  const trendIcon = trend === "up" ? "↑" : trend === "down" ? "↓" : "→";
  const trendClass =
    trend === "up" ? css.trendUp : trend === "down" ? css.trendDown : "";

  if (isLoading && response === undefined) {
    return (
      <div className={css.container}>
        <div className={css.loading}>loading...</div>
      </div>
    );
  }

  return (
    <div className={css.container}>
      <div className={css.row}>
        <button onClick={() => change(-1)} disabled={isPending}
          className={css.buttonDecrement}>−</button>
        <div className={`${css.counter} ${trendClass} ${
          isPending ? css.pending : ""}`}>
          {value}
        </div>
        {trend && <span className={trendClass}>{trendIcon}</span>}
        <button onClick={() => change(1)} disabled={isPending}
          className={css.buttonIncrement}>+</button>
      </div>
      <span className={`${css.syncStatus} ${isPending ? css.visible : ""}`}>
        syncing...
      </span>
    </div>
  );
};
```

`App.module.css` sits next to it and themes through the CSS variables in
the scaffolded `index.css`:

```css
.container { background: var(--color-bg); color: var(--color-text);
  font-family: var(--font-mono); display: flex; flex-direction: column;
  align-items: center; padding: 24px 20px 16px; gap: 12px; }
.row { display: flex; align-items: center; gap: 12px; }
.counter { font-size: 36px; font-weight: bold; transition: color 0.15s ease; }
.pending { opacity: 0.7; }
.trendUp { color: var(--color-green); }
.trendDown { color: var(--color-pink); }
.button { width: 40px; height: 40px; border: none; border-radius: 6px;
  cursor: pointer; }
.button:disabled { cursor: not-allowed; opacity: 0.6; }
.buttonIncrement { composes: button; background: var(--color-green);
  color: var(--color-bg-dark); }
.buttonDecrement { composes: button; background: var(--color-pink);
  color: var(--color-bg-dark); }
.syncStatus { color: var(--color-yellow); font-size: 11px; opacity: 0; }
.syncStatus.visible { opacity: 1; }
.loading { color: var(--color-text-muted); font-size: 12px; }
```

### Other actors: pass an explicit `id`

For a UI declared on `User`, or a component talking to a different
entity than the tool-call target, pass `{ id }`; that overload returns
the handle directly:

```tsx
const relatedPerson = usePerson({ id: relationship.otherPersonId });
```

`useMcpToolData()` from `@reboot-dev/reboot-react` returns the raw tool
input the framework received, for following a chain to another entity.

### Many actors: one composing reader

When a collection is correctly decomposed — each item its own `Type`,
indexed by an `OrderedMap` on the parent (Shape C in
[`state-collections.md`](../../python/references/state-collections.md))
— keep it decomposed and give the front-door type a `Reader` that pages
the index and reads each item; the UI keeps one subscription and the
fan-out runs server-side
([`patterns-cross-actor-reads.md`](../../python/references/patterns-cross-actor-reads.md)).
Declare it `mcp=None`; it feeds the UI, not the AI.

```python
async def dashboard(
    self,
    context: ReaderContext,
    request: User.DashboardRequest,
) -> User.DashboardResponse:
    # `items_index_id` is a field on the parent's state, allocated once
    # in its constructor — never synthesized from the state ID.
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

`setCursor` advances to the next page; to render an ever-growing list,
accumulate `response.items` into component state instead.

## Never

- `const counter = useCounter(); counter.useGet()` — the no-id overload
  returns `{ counter, isLoading }` (since 1.3.0), so `counter.useGet` is
  not a function. Destructure, then render a child that takes
  `UseCounterApi`.
- `counter?.useGet()` behind a condition in the same component — a hook
  called conditionally breaks the rules of hooks. Split the component.
- `show_person=UI(request=...)` on `User` plus `usePerson({ id: personId })`
  from a prop — put the UI on `Person` and use the no-id hook
  ([`api-method-types.md`](api-method-types.md)).
- Flattening a decomposed collection back into `list[Item]` on one actor
  to regain a single subscription — use the composing reader above.
- An unguarded `useMcpApp().sendMessage(...)` — `useMcpApp()` can
  return `null` on early renders while the host connection is set up;
  use `app?.`.
- Importing hooks from anything but `<name>_rbt_react` — the hooks are
  emitted only there.

## Limits

- ID resolution order (1.6.0 generated hook): explicit `{ id }`, then a
  `?<pkg>.v1.<Type>.id=<id>` URL parameter (dev), then the default-ID
  map the framework fills from the tool-call target, keyed by the state's
  full name (`<pkg>.v1.<Type>`). With none, the handle is `undefined` and
  `isLoading` turns `false`.
- The provider renders your UI immediately; nothing waits for the host
  to deliver the tool input, so the first renders see `isLoading: true`.

## Scales as

- One composing reader replaces N per-item subscriptions; subscription
  costs and the ~15-per-page threshold are in
  [`patterns-react-state.md`](../../python/references/patterns-react-state.md).

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `state ID must have a length of at least 1` | An explicit-id hook got `id: ''` | Mount the component only once the id is real |

## See also

- [`react-generated-client.md`](../../python/references/react-generated-client.md) — hook and mutation shapes
- [`api-method-types.md`](api-method-types.md) — where each `UI()` lives
- [`patterns-react-state.md`](../../python/references/patterns-react-state.md) — client state, subscription budget
