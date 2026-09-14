#!/usr/bin/env bash
set -Eeuo pipefail

repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
hermes_home=${HERMES_HOME:-$HOME/.hermes}
checkout=${HERMES_CHECKOUT:-$hermes_home/hermes-agent}
tag=
apply=0

usage() {
  echo "Usage: $0 --tag EXACT_RELEASE_TAG [--apply]" >&2
}

while (($#)); do
  case "$1" in
    --tag) [[ $# -ge 2 ]] || { usage; exit 2; }; tag=$2; shift 2 ;;
    --apply) apply=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) usage; exit 2 ;;
  esac
done

[[ $tag =~ ^v[0-9]{4}\.[0-9]+\.[0-9]+([.-][0-9A-Za-z.-]+)?$ ]] || {
  echo "An exact reviewed release tag is required." >&2
  exit 2
}
[[ -d $checkout/.git ]] || { echo "Managed Hermes checkout not found: $checkout" >&2; exit 1; }
[[ -z $(git -C "$checkout" status --porcelain --untracked-files=all) ]] || {
  echo "Refusing to update a dirty Hermes checkout." >&2
  exit 1
}

current_commit=$(git -C "$checkout" rev-parse HEAD)
echo "Current commit: $current_commit"
echo "Requested reviewed tag: $tag"
echo "The operation will back up state, fetch tags, detach at the exact tag, reinstall from that checkout, and validate."
if (( apply == 0 )); then
  echo "Preview only. Review upstream release notes and re-run with --apply."
  exit 0
fi

command -v uv >/dev/null 2>&1 || { echo "uv is required by the managed Hermes install." >&2; exit 1; }
if [[ -x $checkout/venv/bin/python ]]; then
  venv_python="$checkout/venv/bin/python"
elif [[ -x $checkout/.venv/bin/python ]]; then
  venv_python="$checkout/.venv/bin/python"
else
  echo "Managed Hermes venv not found below $checkout." >&2
  exit 1
fi
venv_dir=$(dirname -- "$(dirname -- "$venv_python")")

sync_managed_environment() {
  (
    cd "$checkout"
    unset UV_NO_CONFIG UV_CONFIG_FILE
    UV_PROJECT_ENVIRONMENT="$venv_dir" UV_PYTHON="$venv_python" \
      uv sync --extra all --locked
  )
}

"$repo_root/scripts/backup.sh"
systemctl --user stop hermes-dashboard.service hermes-gateway.service
upgrade_succeeded=0

rollback() {
  local status=$?
  if (( upgrade_succeeded == 0 )); then
    echo "Hermes upgrade failed; restoring commit $current_commit." >&2
    systemctl --user stop hermes-dashboard.service hermes-gateway.service || true
    git -C "$checkout" checkout --detach "$current_commit" || true
    git -C "$checkout" submodule update --init --recursive || true
    sync_managed_environment || true
  fi
  systemctl --user start hermes-gateway.service hermes-dashboard.service || true
  exit "$status"
}
trap rollback EXIT

git -C "$checkout" fetch --no-tags origin "refs/tags/$tag:refs/tags/$tag"
if git -C "$checkout" rev-parse --is-shallow-repository | grep -qx true; then
  git -C "$checkout" fetch --filter=blob:none --unshallow origin
fi
tag_commit=$(git -C "$checkout" rev-list -n 1 "$tag" 2>/dev/null || true)
[[ -n $tag_commit ]] || { echo "Release tag was not found: $tag" >&2; exit 1; }
[[ $tag_commit != "$current_commit" ]] || { echo "Hermes is already at $tag." >&2; exit 1; }
git -C "$checkout" merge-base --is-ancestor "$current_commit" "$tag_commit" || {
  echo "Refusing a downgrade or release that is not descended from the installed commit." >&2
  exit 1
}
git -C "$checkout" checkout --detach "$tag_commit"
git -C "$checkout" submodule update --init --recursive
sync_managed_environment

for profile in default researcher coder reviewer wiki-maintainer web-scraper web-monitor; do
  if [[ $profile == default ]]; then hermes config check; else hermes -p "$profile" config check; fi
done
APPROVED_HERMES_TAG="$tag" "$repo_root/scripts/verify-hermes-pin.sh"
systemctl --user start hermes-gateway.service hermes-dashboard.service
APPROVED_HERMES_TAG="$tag" "$repo_root/scripts/validate.sh" --no-soak
upgrade_succeeded=1
trap - EXIT
echo "Hermes upgraded and pinned to $tag ($tag_commit)."
