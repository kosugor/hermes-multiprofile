#!/usr/bin/env bash
set -Eeuo pipefail

hermes_home=${HERMES_HOME:-$HOME/.hermes}
checkout="$hermes_home/profiles/coder/plugins/hermes-lcm"
approved_tag=v1.0.0-rc.1
approved_commit=8d1b1e6d3d63f5fc7b209e8d7ec1dc9b814f2e54
approved_origin=https://github.com/stephenschoettler/hermes-lcm.git

[[ ! -L $checkout && -d $checkout/.git ]] || {
  echo "Coder LCM checkout is missing or is not a direct Git directory: $checkout" >&2
  exit 1
}

head_commit=$(git -C "$checkout" rev-parse HEAD)
origin=$(git -C "$checkout" remote get-url origin 2>/dev/null || true)
[[ $origin == "$approved_origin" ]] || {
  echo "Coder LCM checkout has an unapproved origin: ${origin:-none}" >&2
  exit 1
}
[[ $head_commit == "$approved_commit" ]] || {
  echo "Coder LCM checkout is not pinned to $approved_tag ($approved_commit); found $head_commit." >&2
  exit 1
}

if [[ -n $(git -C "$checkout" status --porcelain --untracked-files=all) ]]; then
  echo "Coder LCM checkout has local changes; a deployment pin must be clean." >&2
  exit 1
fi

grep -Fxq 'name: hermes-lcm' "$checkout/plugin.yaml" || {
  echo "Coder LCM plugin manifest has the wrong name." >&2
  exit 1
}
grep -Fxq 'version: 1.0.0-rc.1' "$checkout/plugin.yaml" || {
  echo "Coder LCM plugin manifest has the wrong version." >&2
  exit 1
}

echo "Coder LCM checkout is clean and pinned to $approved_tag ($head_commit)."
