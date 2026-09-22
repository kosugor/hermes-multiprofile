#!/usr/bin/env bash
set -Eeuo pipefail

repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
lock_file="$repo_root/infra/images.lock.env"

[[ -f $lock_file ]] || { echo "Missing committed image lock: $lock_file" >&2; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "docker is required" >&2; exit 1; }

# shellcheck disable=SC1090
source "$lock_file"
image_vars=(
  SEARXNG_IMAGE VALKEY_IMAGE FIRECRAWL_IMAGE PLAYWRIGHT_IMAGE
  NUQ_POSTGRES_IMAGE REDIS_IMAGE RABBITMQ_IMAGE SANDBOX_BASE_IMAGE
)

for image_var in "${image_vars[@]}"; do
  image=${!image_var:-}
  [[ $image =~ ^[^[:space:]@]+@sha256:[0-9a-f]{64}$ ]] || {
    echo "$image_var is not pinned by sha256 digest." >&2
    exit 1
  }
  docker pull --platform linux/arm64 "$image"
  [[ $(docker image inspect --format '{{.Architecture}}' "$image") == arm64 ]] || {
    echo "$image did not resolve to an ARM64 image." >&2
    exit 1
  }
done

echo "All committed image locks resolve to linux/arm64."
