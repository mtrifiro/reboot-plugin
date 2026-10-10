#!/usr/bin/env sh
#
# Ensure a pinned `uv` (and its sibling `uvx`) is cached in the plugin's
# data dir. On success, prints the absolute path of the directory
# containing the binaries to stdout; status messages go to stderr.
# Sourced indirectly by the `bin/uv` and `bin/uvx` shims.
#
# Source: the platform's tarball from the `astral-sh/uv` GitHub
# release, verified against the SHA-256 pinned here. Not Astral's
# `install.sh`: a script fetched at run time and piped to `sh` cannot
# be verified, and the tarball is what it downloads anyway.

set -eu

# Pinned uv version. To bump, change here, refresh the digests below
# (each release asset has a `.sha256` sibling at
# https://github.com/astral-sh/uv/releases/download/<version>/) and
# update the README.
UV_VERSION="0.11.13"
SHA256_DARWIN_ARM64="196a58aa24da89144187670df7c407358028984537fbc2f8f2d8f7a2604980df"
SHA256_DARWIN_X64="99aad3f4956f5b92efd83eca6d87bf03e10688899487ad541f904c9c25c61dc1"
SHA256_LINUX_X64="f830ea3d38ae1492acf53cb7f2cd0f81d6ae22b42d2d7310a6c7d42c451e1a43"
SHA256_LINUX_ARM64="12366407dc1fdba5179b10bd69c11ebfc2eff25791366089c0b2f5701056efc5"

# `PLUGIN_DATA` is hardcoded rather than read from `$CLAUDE_PLUGIN_DATA`.
# Claude Code only sets that env var when it runs something from a
# plugin entry point — e.g. a hook command. It is *not* set when the
# agent runs a binary directly via its Bash tool, even when that binary
# happens to be a shim we ship in `bin/`. Honoring it would mean shims
# invoked from a hook write to one cache and shims invoked directly by
# the agent write to another, double-downloading the tooling. Pinning
# a fixed path keeps one shared cache.
PLUGIN_DATA="$HOME/.claude/plugins/data/reboot"
UV_DIR="$PLUGIN_DATA/bin/uv-$UV_VERSION"

# Hot path: both binaries cached.
if [ -x "$UV_DIR/uv" ] && [ -x "$UV_DIR/uvx" ]; then
    printf '%s\n' "$UV_DIR"
    exit 0
fi

# Detect platform in uv's release-asset naming (glibc on Linux, as
# Node's official tarballs also require).
os_name="$(uname -s)"
arch_name="$(uname -m)"
case "$os_name-$arch_name" in
    Linux-x86_64 | Linux-amd64) TARGET=x86_64-unknown-linux-gnu; EXPECTED_SHA256="$SHA256_LINUX_X64" ;;
    Linux-aarch64 | Linux-arm64) TARGET=aarch64-unknown-linux-gnu; EXPECTED_SHA256="$SHA256_LINUX_ARM64" ;;
    Darwin-arm64) TARGET=aarch64-apple-darwin; EXPECTED_SHA256="$SHA256_DARWIN_ARM64" ;;
    Darwin-x86_64) TARGET=x86_64-apple-darwin; EXPECTED_SHA256="$SHA256_DARWIN_X64" ;;
    *)
        printf '\033[1;31m[reboot-plugin]\033[0m unsupported platform for uv: %s-%s\n' \
            "$os_name" "$arch_name" >&2
        exit 1
        ;;
esac

# Cold path: download the tarball, verify, extract into a staging dir,
# atomically rename into place. If a concurrent invocation wins the
# race, our staged copy is discarded by the trap.
mkdir -p "$PLUGIN_DATA/bin"
STAGE="$PLUGIN_DATA/bin/.uv-$UV_VERSION.$$"
rm -rf "$STAGE"
# `$STAGE` is expanded now (when the trap is set), so it stays
# correct even if the variable is later reassigned.
# shellcheck disable=SC2064
trap "rm -rf '$STAGE'" EXIT INT TERM
mkdir -p "$STAGE"

START_SECONDS=$(date +%s)
printf '\033[1;34m[reboot-plugin]\033[0m installing pinned uv %s into %s ...\n' \
    "$UV_VERSION" "$UV_DIR" >&2

# Verify a downloaded file's SHA-256 against the pinned digest. Without
# a tool to compute it, nothing is installed: an unverified download is
# not what the pin promises.
_verify_sha256() {
    _file="$1"
    _expected="$2"
    if command -v sha256sum >/dev/null 2>&1; then
        _actual="$(sha256sum "$_file" | awk '{print $1}')"
    elif command -v shasum >/dev/null 2>&1; then
        _actual="$(shasum -a 256 "$_file" | awk '{print $1}')"
    elif command -v openssl >/dev/null 2>&1; then
        _actual="$(openssl dgst -sha256 "$_file" | awk '{print $NF}')"
    else
        printf '\033[1;31m[reboot-plugin]\033[0m no sha256sum, shasum or openssl to verify uv %s; not installing\n' \
            "$UV_VERSION" >&2
        exit 1
    fi
    if [ "$_expected" != "$_actual" ]; then
        printf '\033[1;31m[reboot-plugin]\033[0m uv SHA-256 mismatch (expected %s, got %s)\n' \
            "$_expected" "$_actual" >&2
        exit 1
    fi
}

tarball="uv-${TARGET}.tar.gz"
curl -fsSL --output "$STAGE/$tarball" \
    "https://github.com/astral-sh/uv/releases/download/${UV_VERSION}/${tarball}"
_verify_sha256 "$STAGE/$tarball" "$EXPECTED_SHA256"

# The tarball holds `uv-<target>/uv` and `uv-<target>/uvx`; strip the
# directory so they land directly in `$STAGE`.
tar -xzf "$STAGE/$tarball" -C "$STAGE" --strip-components=1
rm -f "$STAGE/$tarball"
chmod +x "$STAGE/uv" "$STAGE/uvx"

# Atomically place the staged dir at `$UV_DIR`. If `$UV_DIR`
# already exists, `mv` to a directory would move-INTO rather
# than rename, so guard with an explicit existence check. The
# tiny race window between check and `mv` could leave a stray
# `.uv-<version>.<pid>` subdir inside `$UV_DIR`; that's cosmetic
# and doesn't affect correctness, since the cached binaries are
# still at the expected paths either way.
if [ ! -e "$UV_DIR" ]; then
    mv "$STAGE" "$UV_DIR" 2>/dev/null || :
fi

if [ ! -x "$UV_DIR/uv" ] || [ ! -x "$UV_DIR/uvx" ]; then
    printf '\033[1;31m[reboot-plugin]\033[0m failed to install uv %s\n' \
        "$UV_VERSION" >&2
    exit 1
fi

printf '\033[1;34m[reboot-plugin]\033[0m installed pinned uv %s in %ds\n' \
    "$UV_VERSION" "$(($(date +%s) - START_SECONDS))" >&2

printf '%s\n' "$UV_DIR"
