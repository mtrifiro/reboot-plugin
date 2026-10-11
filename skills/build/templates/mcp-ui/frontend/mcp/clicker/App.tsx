import { useState, type FC } from "react";
import {
  type UseCounterApi,
  useCounter,
} from "@api/__app__/v1/__app___rbt_react";
import { useHostTheme } from "../host-theme";
import css from "./App.module.css";

// `Counter.show=UI(...)` puts this UI on `Counter`, so the zero-arg
// `useCounter()` resolves the counter the AI's tool call targeted. It
// returns `{ counter, isLoading }`; `counter` is `undefined` until the
// id resolves.
export const CounterApp: FC = () => {
  useHostTheme();
  const { counter } = useCounter();
  if (counter === undefined) {
    return <Skeleton />;
  }
  return <CounterView counter={counter} />;
};

// Mounted only once `counter` exists, so its hooks always have a real id.
const CounterView: FC<{ counter: UseCounterApi }> = ({ counter }) => {
  const { response, isLoading } = counter.useGet();
  const [isPending, setIsPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const increment = async () => {
    setIsPending(true);
    // Mutations resolve to `{ response, aborted }`; they never throw.
    const { aborted } = await counter.increment({ amount: 1 });
    setError(aborted ? aborted.message : null);
    setIsPending(false);
  };

  if (isLoading && response === undefined) {
    return <Skeleton />;
  }

  return (
    <main className="ui">
      <section className="panel" aria-labelledby="counter-label">
        <h2 id="counter-label">Counter</h2>
        <div className={css.value}>{response?.value ?? 0}</div>
        <button className="primary" onClick={increment} disabled={isPending}>
          Increment
        </button>
        {error !== null && <p className="error">{error}</p>}
      </section>
    </main>
  );
};

// Shaped like the real panel, so the frame doesn't jump when it loads.
const Skeleton: FC = () => (
  <main className="ui" aria-busy="true">
    <section className="panel">
      <div className="skeleton" style={{ width: 96, height: 18 }} />
      <div className="skeleton" style={{ width: 64, height: 48, margin: "12px 0" }} />
      <div className="skeleton" style={{ width: 110, height: 34 }} />
    </section>
  </main>
);
