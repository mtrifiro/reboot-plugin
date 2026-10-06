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
// with a real id. The page anatomy every page follows: a title block on
// the brand band (what the page is for, what to do here, the main
// action), then the summary overlapping the band's edge, then the content.
function SignedIn({ user }: { user: UseUserApi }) {
  const { response } = user.useGet();
  return (
    <>
      <div className="brand-band">
        <div className="page-head">
          <div>
            <h1>__Title__</h1>
            <p className="lede">Your own count, saved to your account.</p>
          </div>
          <div className="actions">
            <button className="primary" onClick={() => user.increment({ amount: 1 })}>
              Increment
            </button>
          </div>
        </div>
      </div>
      <main>
        <section className="stats" aria-label="Summary">
          <div className="stat">
            <div className="label">Count</div>
            {response === undefined ? (
              <div className="skeleton" style={{ width: 64, height: 34 }} />
            ) : (
              <div className="value" data-testid="count">
                {response.value ?? 0}
              </div>
            )}
          </div>
        </section>
      </main>
    </>
  );
}
