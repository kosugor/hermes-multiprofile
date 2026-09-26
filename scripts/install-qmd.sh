#!/usr/bin/env bash
set -Eeuo pipefail

repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
hermes_home=${HERMES_HOME:-$HOME/.hermes}
qmd_version=2.8.3
qmd_integrity='sha512-zjfVwrObPB618B6x8SdhlGv/tX9OxRHsbQnr5DUtBvqPK6HGQ27lM+9/BAY5okpjrHVnW56hLyDkqoTcsrVLzA=='
runtime="$hermes_home/qmd-runtime"
qmd_bin="$runtime/node_modules/.bin/qmd"
qmd_config_dir="$hermes_home/profiles/wiki-maintainer/qmd"
managed_node="$hermes_home/node/bin"

[[ $EUID -ne 0 ]] || { echo "Run as the dedicated unprivileged Hermes user." >&2; exit 1; }
[[ $hermes_home == "$HOME/.hermes" ]] || {
  echo "This bundle requires HERMES_HOME=$HOME/.hermes." >&2
  exit 1
}
[[ $(uname -m) == aarch64 || $(uname -m) == arm64 ]] || {
  echo "This QMD installation is reviewed for ARM64 only." >&2
  exit 1
}
[[ -x $managed_node/node && -x $managed_node/npm ]] || {
  echo "Hermes-managed Node.js/npm is missing; run scripts/install-hermes.sh first." >&2
  exit 1
}
node_major=$("$managed_node/node" -p 'process.versions.node.split(".")[0]')
(( node_major >= 22 )) || {
  echo "QMD $qmd_version requires Node.js 22 or newer." >&2
  exit 1
}
[[ -d $hermes_home/profiles/wiki-maintainer ]] || {
  echo "Create the Wiki Maintainer profile before installing QMD." >&2
  exit 1
}

export PATH="$managed_node:$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin"
export QMD_CONFIG_DIR="$qmd_config_dir"
export QMD_FORCE_CPU=1

install -d -m 0755 "$runtime" "$qmd_config_dir" "$HOME/.cache/qmd"
install -m 0644 "$repo_root/qmd/package.json" "$runtime/package.json"
install -m 0644 "$repo_root/qmd/package-lock.json" "$runtime/package-lock.json"
install -m 0644 "$repo_root/qmd/wiki-index.yml" "$qmd_config_dir/index.yml"

installed_version=
if [[ -f $runtime/node_modules/@tobilu/qmd/package.json ]]; then
  installed_version=$(
    "$managed_node/node" -p \
      "require(process.argv[1]).version" \
      "$runtime/node_modules/@tobilu/qmd/package.json" 2>/dev/null || true
  )
fi
lock_sha256=$(sha256sum "$repo_root/qmd/package-lock.json" | awk '{print $1}')
installed_lock_sha256=$(cat "$runtime/.package-lock.sha256" 2>/dev/null || true)
if [[ $installed_version != "$qmd_version" \
  || ! -x $qmd_bin \
  || $installed_lock_sha256 != "$lock_sha256" ]]; then
  "$managed_node/npm" ci --omit=dev --no-audit --no-fund --prefix "$runtime"
  printf '%s\n' "$lock_sha256" > "$runtime/.package-lock.sha256"
fi

locked_integrity=$(
  "$managed_node/node" -p \
    "require(process.argv[1]).packages['node_modules/@tobilu/qmd'].integrity" \
    "$runtime/package-lock.json"
)
[[ $locked_integrity == "$qmd_integrity" ]] || {
  echo "The QMD package integrity lock did not match the reviewed value." >&2
  exit 1
}

# Build the lexical index immediately and generate embeddings for changed
# documents. QMD keeps its rebuildable index and models below ~/.cache/qmd;
# only the reviewed collection configuration lives in the profile backup.

"$qmd_bin" pull

# QMD materializes model defaults and reformats index.yml during pull.
# Restore the reviewed configuration before performing the exact comparison.
install -m 0644 \
  "$repo_root/qmd/wiki-index.yml" \
  "$qmd_config_dir/index.yml"

"$repo_root/scripts/verify-qmd-pin.sh"


"$qmd_bin" update
"$qmd_bin" embed --timeout 60

echo "Installed QMD $qmd_version and indexed /srv/hermes/wiki for Wiki Maintainer."
