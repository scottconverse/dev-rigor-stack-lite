#!/usr/bin/env sh
set -eu

usage() {
  echo "usage: ./install.sh TARGET [--force] [--goals DIR] [--anchor FILE]" >&2
  echo "  TARGET        directory to copy the 19 skills into" >&2
  echo "  --force       replace skills that already exist in TARGET" >&2
  echo "  --goals DIR   also install the rigor-goals tool into DIR" >&2
  echo "  --anchor FILE create or refresh the managed anchor block in FILE" >&2
  echo "                (an agent instructions file: CLAUDE.md, AGENTS.md, GEMINI.md)" >&2
  exit 2
}

[ "$#" -ge 1 ] || usage
target=$1; shift
force=""; goals_dir=""; anchor_file=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --force)  force="--force"; shift ;;
    --goals)  [ "$#" -ge 2 ] || usage; goals_dir=$2; shift 2 ;;
    --anchor) [ "$#" -ge 2 ] || usage; anchor_file=$2; shift 2 ;;
    *) echo "unknown option: $1" >&2; usage ;;
  esac
done

repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
mkdir -p "$target"

for source in "$repo_dir"/skills/*; do
  [ -d "$source" ] || continue
  name=${source##*/}
  destination=$target/$name
  if [ -e "$destination" ]; then
    if [ "$force" != "--force" ]; then
      echo "skill already exists: $destination (use --force to replace)" >&2
      exit 1
    fi
    rm -rf -- "$destination"
  fi
  cp -R -- "$source" "$destination"
done
echo "Installed 19 hook-free skills to $target"

if [ -n "$goals_dir" ]; then
  mkdir -p "$goals_dir"
  cp -- "$repo_dir/tools/rigor_goals.py" "$goals_dir/rigor_goals.py"
  chmod +x "$goals_dir/rigor_goals.py" 2>/dev/null || true
  echo "Installed rigor-goals to $goals_dir/rigor_goals.py (run: python3 $goals_dir/rigor_goals.py)"
fi

if [ -n "$anchor_file" ]; then
  anchor_src=$repo_dir/anchor/anchor.md
  begin_marker='<!-- dev-rigor-lite anchor'
  end_marker='<!-- /dev-rigor-lite anchor -->'
  if [ -f "$anchor_file" ] && grep -qF "$begin_marker" "$anchor_file"; then
    if ! grep -qF "$end_marker" "$anchor_file"; then
      echo "anchor block in $anchor_file has a begin marker but no end marker — fix it by hand first" >&2
      exit 1
    fi
    # Replace the managed block in place; hand edits outside the markers survive.
    # CRs are stripped from the source lines here AND on first append (below), so
    # a CRLF checkout (core.autocrlf=true) cannot make the first refresh report a
    # spurious change. (Gate finding, 0.2.1.)
    tmp=$(mktemp)
    awk -v begin="$begin_marker" -v end="$end_marker" -v src="$anchor_src" '
      index($0, begin) == 1 { skipping = 1; while ((getline line < src) > 0) { sub(/\r$/, "", line); print line }; close(src); next }
      skipping && index($0, end) == 1 { skipping = 0; next }
      !skipping { print }
    ' "$anchor_file" > "$tmp"
    if command -v diff >/dev/null 2>&1 && diff -q "$anchor_file" "$tmp" >/dev/null 2>&1; then
      rm -f "$tmp"
      echo "Anchor block in $anchor_file is already current"
    else
      command -v diff >/dev/null 2>&1 && { echo "Anchor block change:"; diff "$anchor_file" "$tmp" || true; }
      mv "$tmp" "$anchor_file"
      echo "Anchor block refreshed in $anchor_file"
    fi
  else
    { [ -f "$anchor_file" ] && [ -s "$anchor_file" ] && printf '\n'; tr -d '\r' < "$anchor_src"; } >> "$anchor_file"
    echo "Anchor block added to $anchor_file"
  fi
fi
