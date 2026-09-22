#!/usr/bin/env bash
set -Eeuo pipefail

repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
hermes_home=${HERMES_HOME:-$HOME/.hermes}
plugins_dir="$hermes_home/profiles/coder/plugins"
checkout="$plugins_dir/hermes-lcm"
tag=v1.0.0-rc.1
commit=8d1b1e6d3d63f5fc7b209e8d7ec1dc9b814f2e54
origin=https://github.com/stephenschoettler/hermes-lcm.git

[[ $EUID -ne 0 ]] || { echo "Run as the dedicated unprivileged Hermes user." >&2; exit 1; }
[[ $hermes_home == "$HOME/.hermes" ]] || {
  echo "This bundle requires HERMES_HOME=$HOME/.hermes." >&2
  exit 1
}
command -v git >/dev/null 2>&1 || { echo "git is required." >&2; exit 1; }
[[ -d $hermes_home/profiles/coder ]] || {
  echo "Create the Coder profile before installing LCM." >&2
  exit 1
}

if [[ -e $checkout ]]; then
  "$repo_root/scripts/verify-lcm-pin.sh"
  echo "Coder LCM is already installed at $tag."
  exit 0
fi

mkdir -p "$plugins_dir"
stage=$(mktemp -d "${TMPDIR:-/tmp}/hermes-lcm.XXXXXX")
cleanup() {
  case "$stage" in
    "${TMPDIR:-/tmp}"/hermes-lcm.*) rm -rf -- "$stage" ;;
    *) echo "Refusing to remove unexpected staging path: $stage" >&2 ;;
  esac
}
trap cleanup EXIT

git clone --branch "$tag" --depth 1 "$origin" "$stage/hermes-lcm"
[[ $(git -C "$stage/hermes-lcm" rev-parse HEAD) == "$commit" ]] || {
  echo "The $tag tag did not resolve to the reviewed commit $commit." >&2
  exit 1
}
mv -- "$stage/hermes-lcm" "$checkout"
"$repo_root/scripts/verify-lcm-pin.sh"

echo "Installed Coder LCM $tag at $commit."
