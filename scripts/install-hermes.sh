#!/usr/bin/env bash
set -Eeuo pipefail

repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
hermes_home=${HERMES_HOME:-$HOME/.hermes}
checkout=${HERMES_CHECKOUT:-$hermes_home/hermes-agent}
tag=${APPROVED_HERMES_TAG:-v2026.9.11}
release_commit=${APPROVED_HERMES_COMMIT:-939e45c91d751fadd94dcd1b873ac3cb44846213}
installer_sha256=5854b15670b51a8daae8f59ddfa917062de9f74be261eb73b4b8d719710f8968
installer_url="https://raw.githubusercontent.com/NousResearch/hermes-agent/$tag/scripts/install.sh"
export PATH="$HOME/.local/bin:$PATH"

[[ $EUID -ne 0 ]] || { echo "Run as the dedicated unprivileged Hermes user." >&2; exit 1; }
[[ $hermes_home == "$HOME/.hermes" ]] || {
  echo "This bundle requires HERMES_HOME=$HOME/.hermes." >&2
  exit 1
}
for command_name in curl git sha256sum; do
  command -v "$command_name" >/dev/null 2>&1 || { echo "$command_name is required." >&2; exit 1; }
done

if [[ -d $checkout/.git ]] && [[ -n $(git -C "$checkout" status --porcelain --untracked-files=all) ]]; then
  echo "Refusing to install over a dirty Hermes checkout: $checkout" >&2
  exit 1
fi

if [[ -d $checkout/.git ]] && APPROVED_HERMES_TAG="$tag" "$repo_root/scripts/verify-hermes-pin.sh" >/dev/null 2>&1; then
  echo "Hermes is already installed and pinned to $tag."
  bash "$repo_root/scripts/install-browser.sh"
  exit 0
fi

if [[ $tag != v2026.9.11 || $release_commit != 939e45c91d751fadd94dcd1b873ac3cb44846213 ]]; then
  echo "A fresh install of a different release requires a reviewed installer checksum and bundle update." >&2
  echo "Install the baseline first, then use scripts/upgrade-hermes.sh for a reviewed exact tag." >&2
  exit 1
fi

installer=$(mktemp "${TMPDIR:-/tmp}/hermes-installer.XXXXXX")
cleanup() { rm -f -- "$installer"; }
trap cleanup EXIT
curl --fail --silent --show-error --location "$installer_url" --output "$installer"
printf '%s  %s\n' "$installer_sha256" "$installer" | sha256sum --check --status || {
  echo "The versioned Hermes installer checksum did not match." >&2
  exit 1
}

HERMES_HOME="$hermes_home" bash "$installer" \
  --commit "$release_commit" \
  --force-commit \
  --skip-setup \
  --skip-browser \
  --skip-computer-use \
  --no-skills \
  --non-interactive

git -C "$checkout" fetch --depth=1 origin "refs/tags/$tag:refs/tags/$tag"
[[ $(git -C "$checkout" rev-parse HEAD) == "$release_commit" ]] || {
  echo "Hermes installer did not leave the checkout at $release_commit." >&2
  exit 1
}
APPROVED_HERMES_TAG="$tag" "$repo_root/scripts/verify-hermes-pin.sh"
bash "$repo_root/scripts/install-browser.sh"
echo "Installed Hermes $tag / package 0.21.2 at $release_commit."
