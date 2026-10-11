#!/usr/bin/env sh
# Ensure a pinned Node.js (with bundled `npm` and `npx`) is
# cached in the plugin's data dir. On success, prints the
# absolute path of the Node install root to stdout (binaries
# live in `$NODE_DIR/bin/`); status messages go to stderr.
# Sourced indirectly by the `bin/node` and `bin/npm` shims.

set -eu

# Pinned Node.js version. To bump, change here, refresh the digests
# below from https://nodejs.org/dist/v<version>/SHASUMS256.txt and
# update the README.
NODE_VERSION="22.11.0"
SHA256_LINUX_X64="83bf07dd343002a26211cf1fcd46a9d9534219aad42ee02847816940bf610a72"
SHA256_LINUX_ARM64="6031d04b98f59ff0f7cb98566f65b115ecd893d3b7870821171708cdbaf7ae6e"
SHA256_DARWIN_ARM64="c379a90c6aa605b74042a233ddcda4247b347ba5732007d280e44422cc8f9ecb"
SHA256_DARWIN_X64="ab28d1784625d151e3f608a9412a009118f376118ed842ae643f8c2efdfb0af6"

# `PLUGIN_DATA` is hardcoded rather than read from `$CLAUDE_PLUGIN_DATA`.
# Claude Code only sets that env var when it runs something from a
# plugin entry point — e.g. a hook command. It is *not* set when the
# agent runs a binary directly via its Bash tool, even when that binary
# happens to be a shim we ship in `bin/`. Honoring it would mean shims
# invoked from a hook write to one cache and shims invoked directly by
# the agent write to another, double-downloading the tooling. Pinning
# a fixed path keeps one shared cache.
PLUGIN_DATA="$HOME/.claude/plugins/data/reboot"

# Detect platform in Node's release-tarball naming.
os_name="$(uname -s)"
arch_name="$(uname -m)"
case "$os_name-$arch_name" in
    Linux-x86_64 | Linux-amd64) NODE_PLATFORM=linux-x64; EXPECTED_SHA256="$SHA256_LINUX_X64" ;;
    Linux-aarch64 | Linux-arm64) NODE_PLATFORM=linux-arm64; EXPECTED_SHA256="$SHA256_LINUX_ARM64" ;;
    Darwin-arm64) NODE_PLATFORM=darwin-arm64; EXPECTED_SHA256="$SHA256_DARWIN_ARM64" ;;
    Darwin-x86_64) NODE_PLATFORM=darwin-x64; EXPECTED_SHA256="$SHA256_DARWIN_X64" ;;
    *)
        printf '\033[1;31m[reboot-plugin]\033[0m unsupported platform: %s-%s\n' \
            "$os_name" "$arch_name" >&2
        exit 1
        ;;
esac

NODE_DIR="$PLUGIN_DATA/bin/node-v$NODE_VERSION-$NODE_PLATFORM"

# Hot path: cached binary present.
if [ -x "$NODE_DIR/bin/node" ]; then
    printf '%s\n' "$NODE_DIR"
    exit 0
fi

# Cold path: download tarball, verify SHA-256, extract into a
# staging dir, atomically rename into place.
mkdir -p "$PLUGIN_DATA/bin"
STAGE="$PLUGIN_DATA/bin/.node-v$NODE_VERSION-$NODE_PLATFORM.$$"
rm -rf "$STAGE"
# shellcheck disable=SC2064
trap "rm -rf '$STAGE'" EXIT INT TERM
mkdir -p "$STAGE"

tarball="node-v${NODE_VERSION}-${NODE_PLATFORM}.tar.xz"
base_url="https://nodejs.org/dist/v${NODE_VERSION}"
url="${base_url}/${tarball}"

START_SECONDS=$(date +%s)
printf '\033[1;34m[reboot-plugin]\033[0m installing pinned Node.js %s into %s ...\n' \
    "$NODE_VERSION" "$NODE_DIR" >&2

curl -fsSL --output "$STAGE/$tarball" "$url"

# Verify against the digest pinned above (from the release's
# `SHASUMS256.txt`, fetched once when the pin was set, not at install
# time: a manifest from the same origin as the tarball proves
# nothing). Without a tool to compute it, nothing is installed.
if command -v sha256sum >/dev/null 2>&1; then
    actual="$(sha256sum "$STAGE/$tarball" | awk '{print $1}')"
elif command -v shasum >/dev/null 2>&1; then
    actual="$(shasum -a 256 "$STAGE/$tarball" | awk '{print $1}')"
elif command -v openssl >/dev/null 2>&1; then
    actual="$(openssl dgst -sha256 "$STAGE/$tarball" | awk '{print $NF}')"
else
    printf '\033[1;31m[reboot-plugin]\033[0m no sha256sum, shasum or openssl to verify Node.js %s; not installing\n' \
        "$NODE_VERSION" >&2
    exit 1
fi
if [ "$EXPECTED_SHA256" != "$actual" ]; then
    printf '\033[1;31m[reboot-plugin]\033[0m Node SHA-256 mismatch (expected %s, got %s)\n' \
        "$EXPECTED_SHA256" "$actual" >&2
    exit 1
fi

# Strip the top-level `node-vX.Y.Z-<platform>/` so the contents
# land directly in `$STAGE` (giving us `$STAGE/bin/node`, etc.).
tar -xJf "$STAGE/$tarball" -C "$STAGE" --strip-components=1
rm -f "$STAGE/$tarball"

# Same atomic-rename guard as `install_uv.sh`.
if [ ! -e "$NODE_DIR" ]; then
    mv "$STAGE" "$NODE_DIR" 2>/dev/null || :
fi

if [ ! -x "$NODE_DIR/bin/node" ]; then
    printf '\033[1;31m[reboot-plugin]\033[0m failed to install Node.js %s\n' \
        "$NODE_VERSION" >&2
    exit 1
fi

printf '\033[1;34m[reboot-plugin]\033[0m installed pinned Node.js %s in %ds\n' \
    "$NODE_VERSION" "$(($(date +%s) - START_SECONDS))" >&2

printf '%s\n' "$NODE_DIR"
