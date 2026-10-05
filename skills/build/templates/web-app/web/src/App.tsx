import { useSignIn, useSignOut } from "@reboot-dev/reboot-react";
import { type UseUserApi, useUser } from "./api/__app__/v1/__app___rbt_react";
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
// with a real id.
function SignedIn({ user }: { user: UseUserApi }) {
  const { response } = user.useGet();
  return (
    <main>
      <div className="page-head">
        <h1>__Title__</h1>
      </div>
      <section className="panel" aria-labelledby="count-label">
        <h2 id="count-label">Count</h2>
        {response === undefined ? (
          <div className="skeleton" style={{ width: 64, height: 40 }} />
        ) : (
          <p className="mono" style={{ fontSize: 40, margin: 0 }} data-testid="count">
            {response.value ?? 0}
          </p>
        )}
        <button className="primary" onClick={() => user.increment({ amount: 1 })}>
          Increment
        </button>
      </section>
    </main>
  );
}
