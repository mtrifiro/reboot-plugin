import { useState, type FC } from "react";
import {
  type UseCounterApi,
  useCounter,
} from "@api/__app__/v1/__app___rbt_react";
import css from "./App.module.css";

// `Counter.show=UI(...)` puts this UI on `Counter`, so the zero-arg
// `useCounter()` resolves the counter the AI's tool call targeted. It
// returns `{ counter, isLoading }`; `counter` is `undefined` until the
// id resolves.
export const CounterApp: FC = () => {
  const { counter } = useCounter();
  if (counter === undefined) {
    return <div className={css.container}>loading...</div>;
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
    return <div className={css.container}>loading...</div>;
  }

  return (
    <div className={css.container}>
      <div className={css.value}>{response?.value ?? 0}</div>
      <button onClick={increment} disabled={isPending}>
        Increment
      </button>
      {error !== null && <div className={css.error}>{error}</div>}
    </div>
  );
};
