#!/usr/bin/env bash
#
# upgrade-kernel.sh — re-vendor the pinned kernel from a given commit.
#
# Usage: scripts/upgrade-kernel.sh <sha> [--force]
#
#   <sha>     Commit in the kernel source repo to vendor.
#   --force   Also overwrite files recorded as "modified" in KERNEL_VERSION.
#             Without it, modified files are left untouched and reported.
#
# Portable: POSIX-ish bash, runs on macOS and Linux. No cygpath, no .bat,
# no GNU-only flags. Reads the source repo and the file manifest from the
# KERNEL_VERSION file at the repository root.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
KV="$ROOT/KERNEL_VERSION"

FORCE=0
SHA=""
for arg in "$@"; do
  case "$arg" in
    --force) FORCE=1 ;;
    -*) echo "unknown option: $arg" >&2; exit 2 ;;
    *)
      if [ -n "$SHA" ]; then
        echo "unexpected extra argument: $arg" >&2; exit 2
      fi
      SHA="$arg"
      ;;
  esac
done

if [ -z "$SHA" ]; then
  echo "usage: scripts/upgrade-kernel.sh <sha> [--force]" >&2
  exit 2
fi

if [ ! -f "$KV" ]; then
  echo "KERNEL_VERSION not found at $KV" >&2
  exit 1
fi

SOURCE="$(awk -F': ' '/^source:/ {print $2; exit}' "$KV")"
if [ -z "$SOURCE" ]; then
  echo "no 'source:' line in $KV" >&2
  exit 1
fi

TMP="$(mktemp -d)"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

echo "Cloning $SOURCE ..."
git clone --quiet "$SOURCE" "$TMP/kernel"
# Fetch the exact commit in case it is not reachable from the default clone.
git -C "$TMP/kernel" fetch --quiet origin "$SHA" 2>/dev/null || true
git -C "$TMP/kernel" checkout --quiet "$SHA"
RESOLVED="$(git -C "$TMP/kernel" rev-parse HEAD)"
echo "Checked out $RESOLVED"

copied=0
refused=0
missing=0
refused_list=""

# Read the manifest: every line after the 'files:' marker is "<path> <status>".
in_files=0
while IFS= read -r line || [ -n "$line" ]; do
  if [ "$in_files" -eq 0 ]; then
    case "$line" in
      files:*) in_files=1 ;;
    esac
    continue
  fi
  [ -z "$line" ] && continue
  path="${line%% *}"
  status="${line##* }"
  src="$TMP/kernel/$path"
  dest="$ROOT/$path"
  if [ ! -f "$src" ]; then
    echo "MISSING in kernel@$SHA: $path"
    missing=$((missing + 1))
    continue
  fi
  if [ "$status" = "modified" ] && [ "$FORCE" -eq 0 ]; then
    echo "REFUSED (modified, use --force): $path"
    refused=$((refused + 1))
    refused_list="$refused_list $path"
    continue
  fi
  mkdir -p "$(dirname "$dest")"
  cp "$src" "$dest"
  echo "copied: $path"
  copied=$((copied + 1))
done < "$KV"

# Rewrite commit: and pinned: in KERNEL_VERSION (portable, no sed -i).
NEWDATE="$(date -u +%F)"
tmpkv="$(mktemp)"
awk -v sha="$RESOLVED" -v d="$NEWDATE" '
  /^commit:/ { print "commit: " sha; next }
  /^pinned:/ { print "pinned: " d; next }
  { print }
' "$KV" > "$tmpkv"
cat "$tmpkv" > "$KV"
rm -f "$tmpkv"

echo
echo "Summary: copied=$copied refused=$refused missing=$missing"
if [ "$refused" -gt 0 ]; then
  echo "Refused (modified, not overwritten):"
  for f in $refused_list; do echo "  $f"; done
  echo "Re-run with --force to overwrite these."
fi
echo "KERNEL_VERSION now pinned to commit: $RESOLVED (pinned: $NEWDATE)"
