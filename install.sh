#!/usr/bin/env sh
set -eu

usage() {
  echo "usage: ./install.sh TARGET [--force] [--goals DIR] [--anchor FILE] [--no-goals] [--no-anchor]" >&2
  echo "  TARGET        directory to copy the 19 skills into" >&2
  echo "  --force       replace skills that already exist in TARGET" >&2
  echo "  --goals DIR   override where the rigor-goals tool installs (default: <TARGET>/../tools)" >&2
  echo "  --anchor FILE override which instructions file gets the anchor block" >&2
  echo "                (default: CLAUDE.md/GEMINI.md/AGENTS.md in the current directory," >&2
  echo "                inferred from TARGET)" >&2
  echo "  --no-goals    OWNER-ONLY opt-out: skip the rigor-goals tool" >&2
  echo "  --no-anchor   OWNER-ONLY opt-out: skip the anchor block" >&2
  echo "The anchor and rigor-goals install BY DEFAULT: they are part of the stack, not" >&2
  echo "extras. The opt-outs exist for the human owner; an agent must never pass them" >&2
  echo "on its own initiative." >&2
  exit 2
}

[ "$#" -ge 1 ] || usage
target=$1; shift
force=""; goals_dir=""; anchor_file=""; no_goals=""; no_anchor=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --force)     force="--force"; shift ;;
    --goals)     [ "$#" -ge 2 ] || usage; goals_dir=$2; shift 2 ;;
    --anchor)    [ "$#" -ge 2 ] || usage; anchor_file=$2; shift 2 ;;
    --no-goals)  no_goals=1; shift ;;
    --no-anchor) no_anchor=1; shift ;;
    *) echo "unknown option: $1" >&2; usage ;;
  esac
done

# An opt-out combined with its own explicit override is a contradiction —
# refuse loudly rather than silently picking a winner. (Review finding, 0.3.0.)
if [ -n "$no_goals" ] && [ -n "$goals_dir" ]; then
  echo "conflicting flags: --no-goals and --goals cannot be combined" >&2; exit 2
fi
if [ -n "$no_anchor" ] && [ -n "$anchor_file" ]; then
  echo "conflicting flags: --no-anchor and --anchor cannot be combined" >&2; exit 2
fi

# Default-on: the full stack installs unless the owner opts out.
if [ -z "$no_goals" ] && [ -z "$goals_dir" ]; then
  goals_dir=$(dirname -- "$target")/tools
fi
if [ -z "$no_anchor" ] && [ -z "$anchor_file" ]; then
  # Case-insensitive inference: Windows filesystems are case-insensitive, and
  # install.ps1's -like already matches that way. (Review finding, 0.3.0.)
  target_lc=$(printf '%s' "$target" | tr '[:upper:]' '[:lower:]')
  case "$target_lc" in
    *.claude*) anchor_file=CLAUDE.md ;;
    *.gemini*) anchor_file=GEMINI.md ;;
    *)         anchor_file=AGENTS.md ;;
  esac
fi

repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
mkdir -p "$target"

# Migration (0.3.2): 0.3.1 renamed lite's audit-lite to quick-audit-lite, but an
# upgrade over an old lite install left the stale audit-lite behind, still
# routable. Remove it ONLY if it is identifiably lite's own old copy — the full
# dev-rigor-stack's audit-lite (which escalates to audit-team, not
# audit-team-lite) must never be touched; protecting it is why the rename exists.
old_audit=$target/audit-lite
if [ -f "$old_audit/SKILL.md" ]; then
  if grep -qF "audit-team-lite" "$old_audit/SKILL.md"; then
    rm -rf -- "$old_audit"
    echo "Migrated: removed stale lite-owned audit-lite (renamed to quick-audit-lite in 0.3.1)"
  else
    echo "Note: $old_audit is not lite's old copy (likely the full dev-rigor-stack's) - left untouched"
  fi
fi

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
