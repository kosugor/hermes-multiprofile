#!/usr/bin/env bash
set -Eeuo pipefail

hermes_home=${HERMES_HOME:-$HOME/.hermes}
approved_version=4.14.1
python_bin=${HERMES_PYTHON:-$hermes_home/hermes-agent/venv/bin/python}

[[ -x $python_bin ]] || {
  echo "Managed Hermes Python is missing: $python_bin" >&2
  exit 1
}
[[ -s "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)/langfuse/requirements.txt" ]] || {
  echo "Langfuse lock input is missing or empty." >&2
  exit 1
}
lock_file="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)/langfuse/requirements.txt"
grep -Eq '^langfuse==4\.14\.1 \\$' "$lock_file" || {
  echo "Langfuse lock does not pin version 4.14.1." >&2
  exit 1
}
grep -Eq '^    --hash=sha256:[0-9a-f]{64}$' "$lock_file" || {
  echo "Langfuse lock does not contain package hashes." >&2
  exit 1
}

installed=$(
  "$python_bin" -c 'import importlib.metadata as m; print(m.version("langfuse"))' 2>/dev/null || true
)
[[ $installed == "$approved_version" ]] || {
  echo "Expected Langfuse $approved_version; found ${installed:-missing}." >&2
  exit 1
}

echo "Langfuse SDK is pinned to $approved_version."
