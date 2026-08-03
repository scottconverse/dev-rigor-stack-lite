#!/usr/bin/env sh
set -eu

usage() {
  echo "usage: ./install.sh TARGET [--force] [--goals DIR] [--anchor FILE] [--no-goals] [--no-anchor]" >&2
  echo "  TARGET        directory to copy the 20 skills into" >&2
  echo "  --force       replace skills that already exist in TARGET" >&2
  echo "  --goals DIR   override where the rigor-goals tool installs (default: <TARGET>/../tools)" >&2
  echo "  --anchor FILE override which instructions file gets the anchor block" >&2
  echo "                (default: host instructions file derived from TARGET)" >&2
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

case "$target" in
  /*) target_was_rooted=1; anchor_target=$target ;;
  *)  target_was_rooted=""; anchor_target=$(pwd -L)/$target ;;
esac

# Infer the anchor before canonicalizing the install target. A relative project
# host may be a symlink, but its lexical .claude/.gemini name still determines
# which project instructions file the agent reads.
if [ -z "$no_anchor" ] && [ -z "$anchor_file" ]; then
  target_parent=$(dirname -- "$anchor_target")
  host_directory=$(basename -- "$target_parent" | tr '[:upper:]' '[:lower:]')
  host_parent=$(dirname -- "$target_parent")

  # A rooted target names a user-host location, so its instructions file belongs
  # beside the skills directory. A relative hidden host directory names a project,
  # so its instructions file belongs in that directory's containing project.
  anchor_directory=$target_parent
  if [ -z "$target_was_rooted" ]; then
    case "$host_directory" in
      .claude|.gemini|.agents|.codex) anchor_directory=$host_parent ;;
    esac
  fi
  case "$host_directory" in
    .claude) anchor_file=$anchor_directory/CLAUDE.md ;;
    .gemini) anchor_file=$anchor_directory/GEMINI.md ;;
    *)       anchor_file=$anchor_directory/AGENTS.md ;;
  esac
fi

repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
source_skills=$(CDPATH= cd -- "$repo_dir/skills" && pwd -P)

if [ -e "$target" ] || [ -L "$target" ]; then
  if [ ! -d "$target" ]; then
    echo "skills target exists but is not a directory: $target" >&2
    exit 1
  fi
  target_compare=$(CDPATH= cd -- "$target" && pwd -P)
else
  target_compare=$anchor_target
fi
if [ "$target_compare" = "$source_skills" ]; then
  echo "refusing skills target that aliases bundled source: $target" >&2
  exit 1
fi

# Default-on: the full stack installs unless the owner opts out.
if [ -z "$no_goals" ] && [ -z "$goals_dir" ]; then
  goals_dir=$(dirname -- "$target_compare")/tools
fi

# Preflight every known refusal before the first filesystem mutation. A failed
# install must not leave a mixed skill inventory or a goals-only partial install.
if [ "$force" != "--force" ] && [ -d "$target" ]; then
  collisions=""
  for source in "$repo_dir"/skills/*; do
    [ -d "$source" ] || continue
    destination=$target/${source##*/}
    if [ -e "$destination" ] || [ -L "$destination" ]; then
      collisions="${collisions}${collisions:+, }$destination"
    fi
  done
  if [ -n "$collisions" ]; then
    echo "skill already exists: $collisions (use --force to replace)" >&2
    exit 1
  fi
fi

if [ -n "$goals_dir" ]; then
  if { [ -e "$goals_dir" ] || [ -L "$goals_dir" ]; } && [ ! -d "$goals_dir" ]; then
    echo "goals destination exists but is not a directory: $goals_dir" >&2
    exit 1
  fi
  goals_file=$goals_dir/rigor_goals.py
  if [ -e "$goals_file" ] && [ "$repo_dir/tools/rigor_goals.py" -ef "$goals_file" ]; then
    echo "refusing goals destination that aliases bundled source: $goals_file" >&2
    exit 1
  fi
fi

if [ -n "$anchor_file" ]; then
  anchor_src=$repo_dir/anchor/anchor.md
  if [ -e "$anchor_file" ] && [ "$anchor_src" -ef "$anchor_file" ]; then
    echo "refusing anchor destination that aliases bundled source: $anchor_file" >&2
    exit 1
  fi
  if [ -e "$anchor_file" ] || [ -L "$anchor_file" ]; then
    if [ ! -f "$anchor_file" ]; then
      echo "anchor destination exists but is not a file: $anchor_file" >&2
      exit 1
    fi
    begin_marker='<!-- dev-rigor-lite anchor'
    end_marker='<!-- /dev-rigor-lite anchor -->'
    begin_count=$(grep -cF "$begin_marker" "$anchor_file" || true)
    end_count=$(grep -cF "$end_marker" "$anchor_file" || true)
    if { [ "$begin_count" -eq 0 ] && [ "$end_count" -ne 0 ]; } ||
       { [ "$begin_count" -ne 0 ] && [ "$end_count" -eq 0 ]; }; then
      echo "anchor block in $anchor_file has an incomplete marker pair - fix it by hand first" >&2
      exit 1
    fi
    if [ "$begin_count" -gt 1 ] || [ "$end_count" -gt 1 ]; then
      echo "anchor block in $anchor_file has duplicate markers - fix it by hand first" >&2
      exit 1
    fi
    if [ "$begin_count" -eq 1 ]; then
      begin_line=$(grep -nF "$begin_marker" "$anchor_file" | cut -d: -f1)
      end_line=$(grep -nF "$end_marker" "$anchor_file" | cut -d: -f1)
      if [ "$end_line" -le "$begin_line" ]; then
        echo "anchor block in $anchor_file has markers out of order - fix it by hand first" >&2
        exit 1
      fi
      canonical_begin=$(sed -n '1p' "$anchor_src" | tr -d '\r')
      canonical_end=$(awk 'NF { line=$0 } END { sub(/\r$/, "", line); print line }' "$anchor_src")
      actual_begin=$(sed -n "${begin_line}p" "$anchor_file" | tr -d '\r')
      actual_end=$(sed -n "${end_line}p" "$anchor_file" | tr -d '\r')
      if [ "$actual_begin" != "$canonical_begin" ] || [ "$actual_end" != "$canonical_end" ]; then
        echo "anchor markers in $anchor_file share a line with owner or changed text - fix it by hand first" >&2
        exit 1
      fi
    fi
  fi
fi

mkdir -p "$target"
target=$(CDPATH= cd -- "$target" && pwd -P)

# Migration (0.3.2): 0.3.1 renamed lite's audit-lite to quick-audit-lite, but an
# upgrade over an old lite install left the stale audit-lite behind, still
# routable. Deletion rules (review-hardened):
#   - identity = lite's exact escalation sentence, not a bare name mention —
#     a file that merely *talks about* audit-team-lite must survive;
#   - destructive only under --force, like every other destructive act here
#     (real upgrades pass --force anyway to replace the 20 skill dirs);
#   - case-sensitive, matching install.ps1 exactly.
old_audit=$target/audit-lite
lite_marker='Escalate to `audit-team-lite`'
if [ -f "$old_audit/SKILL.md" ]; then
  if grep -qF "$lite_marker" "$old_audit/SKILL.md"; then
    if [ "$force" = "--force" ]; then
      rm -rf -- "$old_audit"
      echo "Migrated: removed stale lite-owned audit-lite (renamed to quick-audit-lite in 0.3.1)"
    else
      echo "WARNING: stale lite-owned audit-lite detected at $old_audit (renamed to quick-audit-lite in 0.3.1)." >&2
      echo "         Re-run with --force to migrate it, or remove it by hand - until then both may route." >&2
    fi
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
echo "Installed 20 hook-free skills to $target"

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
