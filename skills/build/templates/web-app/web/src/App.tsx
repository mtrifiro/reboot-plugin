import { useSignIn, useSignOut } from "@reboot-dev/reboot-react";
import { type UseUserApi, useUser } from "./api/__app__/v1/__app___rbt_react";

export function App() {
  const { user, isLoading } = useUser();
  const signIn = useSignIn();
  const signOut = useSignOut();
  // `isLoading` covers the `/__/oauth/whoami` session probe.
  if (isLoading) return <p>Loading...</p>;
  if (user === undefined) {
    return <button onClick={() => signIn()}>Sign in</button>;
  }
  return (
    <>
      <button onClick={() => signOut()}>Sign out</button>
      <SignedIn user={user} />
    </>
  );
}

// Mounted only once `user` exists, so every hook below it is called
// with a real id.
function SignedIn({ user }: { user: UseUserApi }) {
  const { response } = user.useGet();
  return (
    <main>
      <h1>__Title__</h1>
      <p data-testid="count">{response?.value ?? 0}</p>
      <button onClick={() => user.increment({ amount: 1 })}>
        Increment
      </button>
    </main>
  );
}
