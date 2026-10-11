#!/usr/bin/env sh
#
# Ensure a pinned Envoy binary is cached in the plugin's data
# dir. On success, prints the absolute path of the directory
# containing the binary to stdout (binary is `$ENVOY_DIR/envoy`);
# status messages go to stderr. Sourced indirectly by the
# `bin/envoy` shim.
#
# Source mix mirrors the Reboot library's resolver:
# - Linux: official `envoyproxy/envoy` GitHub releases (single
#   binary; the SHA-256 pinned below is from the release's signed
#   `checksums.txt.asc`).
# - macOS arm64: Tetrate's archive at `archive.tetratelabs.io`
#   (`.tar.xz` containing the binary). Tetrate is the de facto
#   third-party distributor of Envoy macOS builds — what `func-e`
#   consumes — and is the only practical source upstream Envoy
#   doesn't publish for macOS. It publishes no digest for the
#   tarball, so the one pinned below is of the archive as fetched
#   when the pin was set; it still refuses a changed download.

set -eu

# Pinned Envoy version. Keep in sync with `reboot/settings.py`
# (`ENVOY_VERSION`), which is the library's source of truth for the
# resolver.
ENVOY_VERSION="1.38.4"
# To bump: the Linux digests from
# https://github.com/envoyproxy/envoy/releases/download/v<version>/checksums.txt.asc;
# the macOS one computed from
# https://archive.tetratelabs.io/envoy/download/v<version>/envoy-v<version>-darwin-arm64.tar.xz
# (Tetrate publishes none; this one was taken on 2026-10-10).
SHA256_LINUX_X64="c994c452de131f59c9ec9f4a2fffcc65039f250a38b6279870bb95dac21db0fa"
SHA256_LINUX_ARM64="847bdd681e78f2bfd5e3f84fbfc6afe20a9b41b5453a6bb8d4b6fae9dab3376f"
SHA256_DARWIN_ARM64="bff2714ebde97297571cbbb1c2c79755038806a4a312261271d31ae98431b76b"

# `PLUGIN_DATA` is hardcoded rather than read from `$CLAUDE_PLUGIN_DATA`.
# Claude Code only sets that env var when it runs something from a
# plugin entry point — e.g. a hook command. It is *not* set when the
# agent runs a binary directly via its Bash tool, even when that binary
# happens to be a shim we ship in `bin/`. Honoring it would mean shims
# invoked from a hook write to one cache and shims invoked directly by
# the agent write to another, double-downloading the tooling. Pinning
# a fixed path keeps one shared cache.
PLUGIN_DATA="$HOME/.claude/plugins/data/reboot"
ENVOY_DIR="$PLUGIN_DATA/bin/envoy-v$ENVOY_VERSION"

# Hot path: cached binary present.
if [ -x "$ENVOY_DIR/envoy" ]; then
    printf '%s\n' "$ENVOY_DIR"
    exit 0
fi

# Detect platform.
os_name="$(uname -s)"
arch_name="$(uname -m)"
case "$os_name-$arch_name" in
    Linux-x86_64 | Linux-amd64)
        ENVOY_SOURCE=github
        ENVOY_ARCH=x86_64
        EXPECTED_SHA256="$SHA256_LINUX_X64"
        ;;
    Linux-aarch64 | Linux-arm64)
        ENVOY_SOURCE=github
        ENVOY_ARCH=aarch_64
        EXPECTED_SHA256="$SHA256_LINUX_ARM64"
        ;;
    Darwin-arm64)
        ENVOY_SOURCE=tetrate
        ENVOY_ARCH=darwin-arm64
        EXPECTED_SHA256="$SHA256_DARWIN_ARM64"
        ;;
    *)
        printf '\033[1;31m[reboot-plugin]\033[0m unsupported platform for Envoy: %s-%s\n' \
            "$os_name" "$arch_name" >&2
        exit 1
        ;;
esac

mkdir -p "$PLUGIN_DATA/bin"
STAGE="$PLUGIN_DATA/bin/.envoy-v$ENVOY_VERSION.$$"
rm -rf "$STAGE"
# shellcheck disable=SC2064
trap "rm -rf '$STAGE'" EXIT INT TERM
mkdir -p "$STAGE"

START_SECONDS=$(date +%s)
printf '\033[1;34m[reboot-plugin]\033[0m installing pinned Envoy %s into %s ...\n' \
    "$ENVOY_VERSION" "$ENVOY_DIR" >&2

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
        printf '\033[1;31m[reboot-plugin]\033[0m no sha256sum, shasum or openssl to verify Envoy %s; not installing\n' \
            "$ENVOY_VERSION" >&2
        exit 1
    fi
    if [ "$_expected" != "$_actual" ]; then
        printf '\033[1;31m[reboot-plugin]\033[0m Envoy SHA-256 mismatch (expected %s, got %s)\n' \
            "$_expected" "$_actual" >&2
        exit 1
    fi
}

case "$ENVOY_SOURCE" in
    github)
        binary_name="envoy-${ENVOY_VERSION}-linux-${ENVOY_ARCH}"
        base_url="https://github.com/envoyproxy/envoy/releases/download/v${ENVOY_VERSION}"
        curl -fsSL --output "$STAGE/envoy" "${base_url}/${binary_name}"
        _verify_sha256 "$STAGE/envoy" "$EXPECTED_SHA256"
        chmod +x "$STAGE/envoy"
        ;;
    tetrate)
        tarball="envoy-v${ENVOY_VERSION}-${ENVOY_ARCH}.tar.xz"
        base_url="https://archive.tetratelabs.io/envoy/download/v${ENVOY_VERSION}"
        url="${base_url}/${tarball}"
        curl -fsSL --output "$STAGE/$tarball" "$url"
        _verify_sha256 "$STAGE/$tarball" "$EXPECTED_SHA256"
        tar -xJf "$STAGE/$tarball" -C "$STAGE"
        # Internal layout is `envoy-v<version>-<platform>/bin/envoy`,
        # but use `find` for tolerance across Tetrate releases.
        extracted="$(find "$STAGE" -type f -name envoy -perm -u+x | head -n 1)"
        if [ -z "$extracted" ]; then
            printf '\033[1;31m[reboot-plugin]\033[0m envoy binary not found inside %s\n' \
                "$tarball" >&2
            exit 1
        fi
        mv "$extracted" "$STAGE/envoy.bin"
        rm -rf "${STAGE:?}/$tarball" "${STAGE:?}/envoy-v${ENVOY_VERSION}-${ENVOY_ARCH}"
        mv "$STAGE/envoy.bin" "$STAGE/envoy"
        chmod +x "$STAGE/envoy"
        ;;
esac

# Same atomic-rename guard as `install_uv.sh`.
if [ ! -e "$ENVOY_DIR" ]; then
    mv "$STAGE" "$ENVOY_DIR" 2>/dev/null || :
fi

if [ ! -x "$ENVOY_DIR/envoy" ]; then
    printf '\033[1;31m[reboot-plugin]\033[0m failed to install Envoy %s\n' \
        "$ENVOY_VERSION" >&2
    exit 1
fi

printf '\033[1;34m[reboot-plugin]\033[0m installed pinned Envoy %s in %ds\n' \
    "$ENVOY_VERSION" "$(($(date +%s) - START_SECONDS))" >&2

printf '%s\n' "$ENVOY_DIR"
