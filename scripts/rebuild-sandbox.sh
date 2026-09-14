#!/usr/bin/env bash
set -Eeuo pipefail

repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
image=hermes-sandbox:2026.09.11
apply=0

[[ ${1:-} == --apply ]] && apply=1
if (($# > 1)) || (($# == 1 && apply == 0)); then
  echo "Usage: $0 [--apply]" >&2
  exit 2
fi

python_lock="$repo_root/images/hermes-sandbox/dependencies/python-requirements.lock"
node_lock="$repo_root/images/hermes-sandbox/dependencies/package-lock.json"

if grep -Ev '^[[:space:]]*(#|$)' "$python_lock" | grep -Evq '==.*--hash=sha256:'; then
  echo "Every Python dependency must be version-pinned and hash-pinned." >&2
  exit 1
fi
jq -e '.lockfileVersion == 3' "$node_lock" >/dev/null

echo "Reviewed dependency inputs:"
sha256sum \
  "$repo_root/images/hermes-sandbox/dependencies/apt-packages.txt" \
  "$python_lock" \
  "$repo_root/images/hermes-sandbox/dependencies/package.json" \
  "$node_lock"

if (( apply == 0 )); then
  echo "Preview only. Review the lockfiles and re-run with --apply."
  exit 0
fi

[[ -f "$repo_root/infra/images.lock.env" ]] || "$repo_root/scripts/lock-images.sh"
# shellcheck disable=SC1091
source "$repo_root/infra/images.lock.env"
[[ $SANDBOX_BASE_IMAGE == *@sha256:* ]] || { echo "Sandbox base is not digest-locked." >&2; exit 1; }

docker build --platform linux/arm64 --pull=false \
  --build-arg BASE_IMAGE="$SANDBOX_BASE_IMAGE" \
  -t "$image" "$repo_root/images/hermes-sandbox"
docker run --rm --network none "$image" bash -ceu \
  'git --version; rg --version; jq --version; curl --version; cc --version; cmake --version; ninja --version; shellcheck --version; sqlite3 --version; python --version; node --version; npm --version'
echo "Rebuilt and smoke-tested $image. Existing terminal containers are ephemeral and are not reused."
