#!/usr/bin/env bash
set -Eeuo pipefail

hermes_home=${HERMES_HOME:-$HOME/.hermes}
checkout=${HERMES_CHECKOUT:-$hermes_home/hermes-agent}
approved_tag=${APPROVED_HERMES_TAG:-v2026.9.11}

[[ -d $checkout/.git ]] || { echo "Managed Hermes Git checkout not found: $checkout" >&2; exit 1; }
command -v hermes >/dev/null 2>&1 || { echo "hermes is not on PATH." >&2; exit 1; }
[[ $approved_tag =~ ^v[0-9]{4}\.[0-9]+\.[0-9]+([.-][0-9A-Za-z.-]+)?$ ]] || {
  echo "APPROVED_HERMES_TAG must be an exact release tag." >&2
  exit 1
}

head_commit=$(git -C "$checkout" rev-parse HEAD)
tag_commit=$(git -C "$checkout" rev-list -n 1 "$approved_tag" 2>/dev/null || true)
[[ -n $tag_commit && $head_commit == "$tag_commit" ]] || {
  echo "Hermes checkout is not pinned to $approved_tag (HEAD $head_commit)." >&2
  exit 1
}

if [[ -n $(git -C "$checkout" status --porcelain --untracked-files=all) ]]; then
  echo "Hermes checkout has local changes; a deployment pin must be clean." >&2
  exit 1
fi

echo "Hermes checkout is clean and pinned to $approved_tag ($head_commit)."
