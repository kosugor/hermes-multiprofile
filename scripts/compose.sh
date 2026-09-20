#!/usr/bin/env bash
set -Eeuo pipefail

repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
env_file="$repo_root/infra/.env"
lock_file="$repo_root/infra/images.lock.env"
compose_file="$repo_root/infra/compose.yaml"

[[ -f $env_file ]] || { echo "Missing $env_file; run scripts/bootstrap-user.sh" >&2; exit 1; }
[[ -f $lock_file ]] || { echo "Missing $lock_file; run scripts/lock-images.sh" >&2; exit 1; }

set -a
# shellcheck disable=SC1090
source "$env_file"
# shellcheck disable=SC1090
source "$lock_file"
set +a

action=${1:-ps}
shift || true
case "$action" in
  up)
    exec docker compose -f "$compose_file" --profile extraction up -d --remove-orphans "$@"
    ;;
  core-up)
    exec docker compose -f "$compose_file" up -d "$@"
    ;;
  extraction-up)
    exec docker compose -f "$compose_file" --profile extraction up -d "$@"
    ;;
  extraction-stop)
    exec docker compose -f "$compose_file" --profile extraction stop firecrawl playwright-service rabbitmq nuq-postgres redis "$@"
    ;;
  stop)
    exec docker compose -f "$compose_file" stop "$@"
    ;;
  down)
    exec docker compose -f "$compose_file" down "$@"
    ;;
  *)
    exec docker compose -f "$compose_file" "$action" "$@"
    ;;
esac
