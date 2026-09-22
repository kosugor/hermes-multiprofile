#!/usr/bin/env bash
set -Eeuo pipefail

repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
hermes_home=${HERMES_HOME:-$HOME/.hermes}
checkout=${HERMES_CHECKOUT:-$hermes_home/hermes-agent}
python_bin=${HERMES_PYTHON:-$checkout/venv/bin/python}
requirements="$repo_root/langfuse/requirements.txt"

[[ -x $python_bin ]] || {
  echo "Managed Hermes Python is missing: $python_bin" >&2
  exit 1
}
[[ -s $requirements ]] || {
  echo "Langfuse lock input is missing: $requirements" >&2
  exit 1
}
command -v uv >/dev/null 2>&1 || { echo "uv is required to install Langfuse." >&2; exit 1; }

uv pip install --python "$python_bin" --require-hashes --upgrade -r "$requirements"
HERMES_PYTHON="$python_bin" "$repo_root/scripts/verify-langfuse-pin.sh"
echo "Installed the reviewed Langfuse SDK into the managed Hermes environment."
