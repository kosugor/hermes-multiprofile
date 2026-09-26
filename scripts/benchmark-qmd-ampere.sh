#!/usr/bin/env bash
set -Eeuo pipefail

# Compare QMD's packaged ARM64 binding with the reviewed native/KleidiAI build.
# Run this on the Ampere A1 host after install-qmd.sh has built the native
# binding and the wiki has been embedded.  It does not modify the collection.

hermes_home=${HERMES_HOME:-$HOME/.hermes}
qmd_bin="$hermes_home/qmd-runtime/node_modules/.bin/qmd"
qmd_config_dir="$hermes_home/profiles/wiki-maintainer/qmd"
query=${1:-"Hermes operational knowledge"}
runs=${QMD_BENCH_RUNS:-3}

[[ $(uname -m) == aarch64 || $(uname -m) == arm64 ]] || {
  echo "This benchmark is for ARM64 hosts only." >&2
  exit 1
}
[[ -x $qmd_bin && -f $qmd_config_dir/index.yml ]] || {
  echo "QMD is not installed; run scripts/install-qmd.sh first." >&2
  exit 1
}
[[ $runs =~ ^[1-9][0-9]*$ ]] || {
  echo "QMD_BENCH_RUNS must be a positive integer." >&2
  exit 1
}

run_mode() {
  local label=$1 native_build=$2 run
  echo "$label ($runs vsearch runs)"
  for ((run = 1; run <= runs; run++)); do
    TIMEFORMAT="  run $run: %R s"
    time env \
      "QMD_CONFIG_DIR=$qmd_config_dir" \
      QMD_FORCE_CPU=1 \
      "QMD_AMPERE_NATIVE_BUILD=$native_build" \
      "$qmd_bin" vsearch "$query" -n 5 --json >/dev/null
  done
}

echo "Query: $query"
run_mode "Packaged ARM64 llama.cpp" 0
run_mode "Ampere-native KleidiAI llama.cpp" 1
