#!/usr/bin/env bash
set -Eeuo pipefail

repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)

if (($#)); then
  echo "Usage: $0" >&2
  exit 2
fi

exec "$repo_root/scripts/install-hermes.sh"
