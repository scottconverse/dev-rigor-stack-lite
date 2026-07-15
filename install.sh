#!/usr/bin/env sh
set -eu

if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
  echo "usage: ./install.sh TARGET [--force]" >&2
  exit 2
fi

target=$1
force=${2:-}
case "$force" in ""|--force) ;; *) echo "unknown option: $force" >&2; exit 2;; esac

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
