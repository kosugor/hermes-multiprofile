#!/usr/bin/env bash
set -Eeuo pipefail

repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
hermes_home=${HERMES_HOME:-$HOME/.hermes}
checkout=${HERMES_CHECKOUT:-$hermes_home/hermes-agent}
installer_url=${HERMES_INSTALLER_URL:-https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh}
export PATH="$HOME/.local/bin:$PATH"

[[ $EUID -ne 0 ]] || { echo "Run as the dedicated unprivileged Hermes user." >&2; exit 1; }
[[ $hermes_home == "$HOME/.hermes" ]] || {
  echo "This bundle requires HERMES_HOME=$HOME/.hermes." >&2
  exit 1
}
for command_name in curl git; do
  command -v "$command_name" >/dev/null 2>&1 || { echo "$command_name is required." >&2; exit 1; }
done

sync_managed_environment() {
  local venv_python venv_dir
  if [[ -x $checkout/venv/bin/python ]]; then
    venv_python="$checkout/venv/bin/python"
  elif [[ -x $checkout/.venv/bin/python ]]; then
    venv_python="$checkout/.venv/bin/python"
  else
    echo "Managed Hermes venv not found below $checkout." >&2
    return 1
  fi
  venv_dir=$(dirname -- "$(dirname -- "$venv_python")")
  (
    cd "$checkout"
    unset UV_NO_CONFIG UV_CONFIG_FILE
    UV_PROJECT_ENVIRONMENT="$venv_dir" UV_PYTHON="$venv_python" \
      uv sync --extra all --locked
  )
}

if [[ -d $checkout/.git ]] && [[ -n $(git -C "$checkout" status --porcelain --untracked-files=all) ]]; then
  echo "Refusing to install over a dirty Hermes checkout: $checkout" >&2
  exit 1
fi

installer=$(mktemp "${TMPDIR:-/tmp}/hermes-installer.XXXXXX")
cleanup() { rm -f -- "$installer"; }
trap cleanup EXIT
curl --fail --silent --show-error --location "$installer_url" --output "$installer"

HERMES_HOME="$hermes_home" bash "$installer" \
  --skip-setup \
  --skip-browser \
  --skip-computer-use \
  --no-skills \
  --non-interactive

command -v uv >/dev/null 2>&1 || { echo "uv is required by the managed Hermes install." >&2; exit 1; }
sync_managed_environment
bash "$repo_root/scripts/install-browser.sh"
echo "Installed or updated Hermes from the current upstream installer."
