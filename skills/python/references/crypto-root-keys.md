---
title: Derive Your Own Keys from Reboot's Managed Crypto Root Keys (with Rotation)
impact: HIGH
impactDescription: Deriving keys wrong, or skipping rotation/usage markers, makes data permanently unrecoverable or pins an old root key forever.
tags: crypto, root-keys, hkdf, derive_key, rotation, use_root_key_version, disuse_root_key_version, encryption, signing
summary: "Most apps want `Ciphertext` instead. Otherwise HKDF-derive from `active_version()`, never change `info` / `length` after shipping, and run the rotation loop with `use` / `disuse` root-key-version markers."
step: servicer
applies: [mcp-ui, web-app, backend-only]
always: false
when: "building your own key-derivation feature"
verified: 1.6.0
docs: ""
---

# Derive Your Own Keys from Reboot's Managed Crypto Root Keys

## When you are here

Deriving your own key (HMAC/signing, custom encryption) from the root
secrets in `REBOOT_CRYPTO_ROOT_KEYS` (`rbt dev` and Reboot Cloud set
it). For encryption at rest or crypto-shredding use `Ciphertext`
(`stdlib-ciphertext.md`) instead; it implements everything here.

If you re-derive from `active_version()` every time and never persist
the key or anything encrypted under it, you need only Derive; a
rotation just yields a new key next time. The `watch` loop and
`use_root_key_version` / `disuse_root_key_version` markers are only for
persisted material wrapped under a specific root version.

## Do this

### Derive

```python
from reboot.crypto import root_keys

# `info`: domain separator, one unique stable byte-string per purpose.
key = root_keys.derive_key(
    info=b"my.app.notes-encryption-key",
    version=root_keys.active_version(),
)  # -> 32 bytes (override with length=)
```

| Call | Returns / raises |
| --- | --- |
| `derive_key(*, info: bytes, version: int, length: int = 32)` | HKDF-SHA256 key (`bytes`); keyword-only; raises `UnknownRootKeyVersion` if `version` is not configured |
| `active_version()` | highest configured version; new material uses it |
| `available_versions()` | all configured versions, ascending |

Errors: `root_keys.MissingRootKeys`, `root_keys.MalformedRootKeys`,
`root_keys.UnknownRootKeyVersion`. The env value is comma-separated
`vN:key` entries, conventionally newest-first (`v2:<new>,v1:<old>`;
both present during a rotation); the highest number is active
regardless of order.

### If you persist material: mark usage and rotate

Two idempotent, app-internal writers on the per-app `Application`
singleton record which root versions you hold, so a version with zero
holders can be retired. Mirror them from a `consuming_versions` set in
your state. Mark `use` in the same transaction that first creates
material under a version, only when it is new to your set (no window
before the marker; one write per version, not per key):

```python
import reboot.application
from reboot.aio.contexts import TransactionContext

CONSUMER = "my.app.notes"  # globally unique; namespace per library/instance


class KeyManagerServicer(KeyManager.Servicer):

    async def register(
        self, context: TransactionContext, request: KeyManager.RegisterRequest,
    ) -> KeyManager.RegisterResponse:
        # ... persist your new key, wrapped under `request.version` ...
        if request.version not in self.state.consuming_versions:
            self.state.consuming_versions.append(request.version)
            await reboot.application.ref().use_root_key_version(
                context, consumer=CONSUMER, version=request.version,
            )
        if not self.state.watch_started:
            await self.ref().schedule().watch(context)
            self.state.watch_started = True
        return KeyManager.RegisterResponse()
```

The rotation loop parks until you hold a version older than active,
then uses the new version, migrates, and disuses the old ones. Every
cross-state call carries `.per_iteration(...)` so replays memoize it:

```python
import reboot.application
from reboot.aio.contexts import WorkflowContext
from reboot.aio.workflows import until
from reboot.crypto import root_keys


class KeyManagerServicer(KeyManager.Servicer):

    @classmethod
    async def watch(
        cls, context: WorkflowContext, request: KeyManager.WatchRequest,
    ) -> KeyManager.WatchResponse:
        async for _ in context.loop("Watch"):

            # Bare `read()` on the own ref is allowed in `until`;
            # a truthy return ends the wait.
            async def stale() -> tuple[int, list[int]] | bool:
                key_manager = await KeyManager.ref().read(context)
                active_version = root_keys.active_version()
                stale_versions = [
                    v for v in key_manager.consuming_versions
                    if v < active_version
                ]
                return (
                    (active_version, stale_versions)
                    if stale_versions else False
                )

            active_version, stale_versions = await until("Stale", context, stale)

            # Mark and start consuming the new version BEFORE migrating.
            await reboot.application.ref().per_iteration(
                "Use root key versions"
            ).use_root_key_version(
                context, consumer=CONSUMER, version=active_version
            )

            async def start_consuming(state: KeyManager.State) -> None:
                if active_version not in state.consuming_versions:
                    state.consuming_versions.append(active_version)

            await KeyManager.ref().per_iteration("Save root key versions being consumed").write(
                context, start_consuming,
            )

            # ... re-derive / re-wrap every persisted key onto
            # `active_version` (page it for large keyrings) ...

            # Stop consuming LOCALLY first, then release the markers.
            async def stop_consuming(state: KeyManager.State) -> None:
                for v in stale_versions:
                    if v in state.consuming_versions:
                        state.consuming_versions.remove(v)

            await KeyManager.ref().per_iteration("Stop consuming root key versions").write(
                context, stop_consuming,
            )

            for version in stale_versions:
                await reboot.application.ref().per_iteration(
                    f"Disuse root key version v{version}"
                ).disuse_root_key_version(
                    context, consumer=CONSUMER, version=version
                )
```

## Never

- Hard-coding a `version` for new material — always
  `active_version()`.
- Changing `info` or `length` after shipping — every derived key
  changes, orphaning everything derived or encrypted.
- A bare `consumer` like `"default"` — app-global, so two libraries
  could retire each other's version. Namespace it, per instance if
  several (`f"my.app.notes:{manager_id}"`).
- Disusing the active version — it is always in use.
- Clearing a marker before removing the version from your own
  `consuming_versions`, or adding the version locally before setting
  its marker — markers must stay a superset of what you hold; an early
  disuse loses data.
- `use` / `disuse` from the `watch` loop without `.per_iteration(...)`.
- Rolling your own envelope encryption — use `Ciphertext`.

## Limits

- Keep the old root version in `REBOOT_CRYPTO_ROOT_KEYS` until
  persisted material is re-wrapped; deriving with a removed version
  raises `UnknownRootKeyVersion`.
- A version is retirable only at zero markers. Nothing in the 1.6.0
  Python package acts on the markers; an operator removes the version
  from the env.
- `use_root_key_version` / `disuse_root_key_version` authorize
  `is_app_internal` only (1.6.0 source).
- `root_keys` has no Reboot dependencies and reads the environment on
  every call.

## Scales as

- Not measured. Writes to the shared `Application` singleton are
  O(versions), not O(keys); the migration sweep is O(persisted keys)
  per rotation.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `root key version v` … `is not in 'REBOOT_CRYPTO_ROOT_KEYS'` | `UnknownRootKeyVersion`: the version was never configured or already removed | Derive from `active_version()`; keep old versions until migrated |
| `'REBOOT_CRYPTO_ROOT_KEYS' is not set` | `MissingRootKeys`: running outside `rbt dev` / Cloud without the env var | Provision it (`lifecycle-secrets.md`) |
| `'REBOOT_CRYPTO_ROOT_KEYS' entry` … `is not of the form 'vN:key'` | `MalformedRootKeys` | Fix the env value |

## See also

- [`stdlib-ciphertext.md`](stdlib-ciphertext.md) — the reference implementation; usually what you want
- [`servicer-workflow-loop.md`](servicer-workflow-loop.md) — the `watch` loop's iterations
- [`servicer-workflow-wait.md`](servicer-workflow-wait.md) — `until` for the stale-version park
