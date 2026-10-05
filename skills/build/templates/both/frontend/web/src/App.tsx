import { useSignIn, useSignOut } from "@reboot-dev/reboot-react";
import {
  type UseUserApi,
  useCounter,
  useUser,
} from "@api/__app__/v1/__app___rbt_react";
import { ThemeToggle } from "./theme";

export function App() {
  const { user, isLoading } = useUser();
  const signIn = useSignIn();
  const signOut = useSignOut();
  return (
    <>
      <header className="topbar">
        <span className="brand">__Title__</span>
        <span className="spacer" />
        <ThemeToggle />
        {user !== undefined && (
          <button className="ghost" onClick={() => signOut()}>
            Sign out
          </button>
        )}
      </header>
      {/* `isLoading` covers the `/__/oauth/whoami` session probe. */}
      {isLoading ? (
        <main aria-busy="true">
          <div className="skeleton" style={{ width: 240, height: 28 }} />
        </main>
      ) : user === undefined ? (
        <main>
          <div className="empty">
            <h1>__Title__</h1>
            <div className="actions">
              <button className="primary" onClick={() => signIn()}>
                Sign in
              </button>
            </div>
          </div>
        </main>
      ) : (
        <SignedIn user={user} />
      )}
    </>
  );
}

// Mounted only once `user` exists, so every hook below it is called
// with a real id. The same `User` the MCP UI's tools act on: a counter
// made in Claude shows up here, and the reverse.
function SignedIn({ user }: { user: UseUserApi }) {
  const { response } = user.useListCounters();
  const ids = response?.counterIds;
  const create = (
    <button className="primary" onClick={() => user.createCounter()}>
      New counter
    </button>
  );
  return (
    <main>
      <div className="page-head">
        <h1>__Title__</h1>
        {ids !== undefined && ids.length > 0 && create}
      </div>
      {ids === undefined ? (
        <div className="skeleton" style={{ width: 280, height: 120 }} />
      ) : ids.length === 0 ? (
        <div className="empty">
          <h2>No counters yet</h2>
          <div className="actions">{create}</div>
        </div>
      ) : (
        <div className="cards">
          {ids.map((id, i) => (
            <CounterCard key={id} id={id} label={`Counter ${i + 1}`} />
          ))}
        </div>
      )}
    </main>
  );
}

function CounterCard({ id, label }: { id: string; label: string }) {
  const counter = useCounter({ id });
  const { response } = counter.useGet();
  return (
    <section className="card" aria-label={label}>
      <h2>{label}</h2>
      {response === undefined ? (
        <div className="skeleton" style={{ width: 64, height: 40 }} />
      ) : (
        <p className="mono" style={{ fontSize: 40, margin: 0 }}>
          {response.value ?? 0}
        </p>
      )}
      <button onClick={() => counter.increment({ amount: 1 })}>
        Increment
      </button>
    </section>
  );
}
