#!/usr/bin/env bash
set -Eeuo pipefail

repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
hermes_home=${HERMES_HOME:-$HOME/.hermes}
qmd_version=2.8.3
qmd_integrity='sha512-zjfVwrObPB618B6x8SdhlGv/tX9OxRHsbQnr5DUtBvqPK6HGQ27lM+9/BAY5okpjrHVnW56hLyDkqoTcsrVLzA=='
runtime="$hermes_home/qmd-runtime"
package_json="$runtime/node_modules/@tobilu/qmd/package.json"
package_lock="$runtime/package-lock.json"
qmd_bin="$runtime/node_modules/.bin/qmd"
managed_node="$hermes_home/node/bin/node"
qmd_config="$hermes_home/profiles/wiki-maintainer/qmd/index.yml"
model_dir="$HOME/.cache/qmd/models"

[[ $hermes_home == "$HOME/.hermes" ]] || {
  echo "This bundle requires HERMES_HOME=$HOME/.hermes." >&2
  exit 1
}
[[ -x $managed_node && -x $qmd_bin && -f $package_json && -f $package_lock ]] || {
  echo "The managed QMD runtime is incomplete; run scripts/install-qmd.sh." >&2
  exit 1
}
installed_version=$(
  "$managed_node" -p "require(process.argv[1]).version" "$package_json" 2>/dev/null || true
)
[[ $installed_version == "$qmd_version" ]] || {
  echo "Expected QMD $qmd_version; found ${installed_version:-unknown}." >&2
  exit 1
}
locked_integrity=$(
  "$managed_node" -p \
    "require(process.argv[1]).packages['node_modules/@tobilu/qmd'].integrity" \
    "$package_lock" 2>/dev/null || true
)
[[ $locked_integrity == "$qmd_integrity" ]] || {
  echo "The installed QMD package lock has unreviewed integrity." >&2
  exit 1
}
cmp -s "$repo_root/qmd/package.json" "$runtime/package.json" \
  && cmp -s "$repo_root/qmd/package-lock.json" "$package_lock" || {
  echo "The installed QMD dependency manifests differ from the reviewed lock." >&2
  exit 1
}
[[ -f $qmd_config ]] || {
  echo "The Wiki Maintainer QMD index configuration is missing: $qmd_config" >&2
  exit 1
}
cmp -s "$repo_root/qmd/wiki-index.yml" "$qmd_config" || {
  echo "The installed QMD collection differs from the reviewed Wiki Maintainer configuration." >&2
  exit 1
}

verify_model() {
  local filename=$1 expected_sha256=$2 model_path actual_sha256
  model_path=$(find "$model_dir" -maxdepth 1 -type f -name "*${filename}" -print -quit 2>/dev/null)
  [[ -n $model_path ]] || {
    echo "The pinned QMD model is missing: $filename" >&2
    return 1
  }
  actual_sha256=$(sha256sum "$model_path" | awk '{print $1}')
  [[ $actual_sha256 == "$expected_sha256" ]] || {
    echo "The QMD model checksum did not match: $filename" >&2
    return 1
  }
}

verify_model \
  embeddinggemma-300M-Q8_0.gguf \
  b5ce9d77a3fc4b3b39ccb5643c36777911cc4eb46a66962eadfa3f5f60490d63
verify_model \
  qwen3-reranker-0.6b-q8_0.gguf \
  22c9979ce4fbcdc5acdc310c6641c32797eff1aa980b8f7a2db8a8ea23429a48
verify_model \
  qmd-query-expansion-1.7B-q4_k_m.gguf \
  000dfb1c06efa6a049e9f64ba921c3740e2454f62abab6fa10e77bd30bb2bcc0

echo "QMD $qmd_version, its local models, and the Wiki Maintainer collection are pinned."
