#!/usr/bin/env bash
set -Eeuo pipefail

hermes_home=${HERMES_HOME:-$HOME/.hermes}
agent_browser_version=0.26.0
playwright_version=1.62.1
managed_bin="$hermes_home/node/bin"
agent_browser_bin="$managed_bin/agent-browser"
playwright_bin="$managed_bin/playwright"

[[ $EUID -ne 0 ]] || { echo "Run as the dedicated unprivileged Hermes user." >&2; exit 1; }
[[ $hermes_home == "$HOME/.hermes" ]] || {
  echo "This bundle requires HERMES_HOME=$HOME/.hermes." >&2
  exit 1
}
[[ $(uname -m) == aarch64 || $(uname -m) == arm64 ]] || {
  echo "This browser installation is reviewed for ARM64 only." >&2
  exit 1
}
[[ -x $managed_bin/node && -x $managed_bin/npm ]] || {
  echo "Hermes-managed Node.js/npm is missing; run scripts/install-hermes.sh first." >&2
  exit 1
}

export PATH="$managed_bin:$HOME/.local/bin:$PATH"
installed_agent_browser=$($agent_browser_bin --version 2>/dev/null || true)
installed_playwright=$($playwright_bin --version 2>/dev/null || true)
if [[ $installed_agent_browser != *"$agent_browser_version"* \
  || $installed_playwright != *"$playwright_version"* ]]; then
  "$managed_bin/npm" install --global --prefix "$hermes_home/node" \
    --ignore-scripts --no-audit --no-fund \
    "agent-browser@$agent_browser_version" "playwright@$playwright_version"
fi

[[ $($agent_browser_bin --version 2>/dev/null || true) == *"$agent_browser_version"* ]] || {
  echo "agent-browser $agent_browser_version was not installed correctly." >&2
  exit 1
}
[[ $($playwright_bin --version 2>/dev/null || true) == *"$playwright_version"* ]] || {
  echo "Playwright $playwright_version was not installed correctly." >&2
  exit 1
}

# agent-browser's Chrome-for-Testing downloader has no Linux ARM64 build.
# Ask the pinned Playwright package for its Chromium executable. Searching the
# shared cache can select an older browser installed by another Playwright release.
"$playwright_bin" install chromium
playwright_module="$hermes_home/node/lib/node_modules/playwright"
chromium_bin=$("$managed_bin/node" -e '
  const { registry } = require(require.resolve("playwright-core/lib/server/registry", {
    paths: [process.argv[1]],
  }));
  process.stdout.write(registry.findExecutable("chromium").executablePath());
' "$playwright_module" 2>/dev/null || true)
if [[ -z $chromium_bin ]]; then
  echo "No executable Playwright Chromium build was found after installation." >&2
  exit 1
fi
mkdir -p "$hermes_home/bin"
ln -sfn -- "$chromium_bin" "$hermes_home/bin/chromium"
[[ -x $hermes_home/bin/chromium ]] || {
  echo "The managed Chromium link is not executable." >&2
  exit 1
}

echo "Installed agent-browser $agent_browser_version with Playwright $playwright_version Chromium."
