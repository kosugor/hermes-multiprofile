#!/usr/bin/env bash
set -Eeuo pipefail

# QMD intentionally runs node-llama-cpp in CPU-only mode on Hermes.  Its
# upstream CPU fallback asks only for a packaged binary, so it cannot select a
# source build with Arm-specific CMake options.  Keep this small, version-gated
# patch separate from the installer: npm ci replaces node_modules on upgrades.

runtime=${1:?usage: patch-qmd-for-ampere.sh /path/to/qmd-runtime}
managed_node=${2:?usage: patch-qmd-for-ampere.sh /path/to/qmd-runtime /path/to/node}
qmd_version=2.8.3
package_json="$runtime/node_modules/@tobilu/qmd/package.json"
llm_js="$runtime/node_modules/@tobilu/qmd/dist/llm.js"

[[ -x $managed_node && -f $package_json && -f $llm_js ]] || {
  echo "QMD runtime is incomplete; cannot apply the Ampere llama.cpp patch." >&2
  exit 1
}

installed_version=$("$managed_node" -p "require(process.argv[1]).version" "$package_json")
[[ $installed_version == "$qmd_version" ]] || {
  echo "Ampere llama.cpp patch is reviewed only for QMD $qmd_version; found $installed_version." >&2
  exit 1
}

"$managed_node" - "$llm_js" <<'NODE'
const fs = require("node:fs");
const file = process.argv[2];
let source = fs.readFileSync(file, "utf8");
const marker = "QMD_AMPERE_NATIVE_BUILD";

if (source.includes(marker)) process.exit(0);

const loaderPattern = /^([ \t]*)const loadLlama = async \(\s*gpu,\s*sourceBuildAllowed = canBuild,\s*buildOverride\s*\) =>\s*/m;
const loaderMatch = source.match(loaderPattern);
if (!loaderMatch) {
  throw new Error("QMD llama loader changed; refusing to apply an unreviewed Ampere patch");
}
const indent = loaderMatch[1];
const addition = [
  "// Hermes enables this only on Ampere Altra (Neoverse-N1) hosts.",
  "// A matching local build is selected even when the service sandbox makes",
  "// node_modules read-only; installation primes it before the service starts.",
  "const useAmpereNativeBuild = process.env.QMD_AMPERE_NATIVE_BUILD === \"1\";",
  "const ampereCmakeOptions = useAmpereNativeBuild ? {",
  "  GGML_NATIVE: \"ON\",",
  "  GGML_CPU_KLEIDIAI: \"ON\"",
  "} : undefined;",
].map((line) => indent + line).join("\n") + "\n";
source = source.replace(loaderPattern, addition + loaderMatch[0]);

const buildOptionsPattern = /^([ \t]*)build:\s*buildOverride\s*\?\?\s*\(sourceBuildAllowed\s*\?\s*\"auto\"\s*:\s*\"never\"\),\s*$/m;
const buildOptionsMatch = source.match(buildOptionsPattern);
const optionsAddition = [
  "cmakeOptions: ampereCmakeOptions,",
  "existingPrebuiltBinaryMustMatchBuildOptions: useAmpereNativeBuild,",
].map((line) => (buildOptionsMatch ? buildOptionsMatch[1] : "") + line).join("\n") + "\n";
if (!buildOptionsMatch) {
  throw new Error("QMD build options changed; refusing to apply an unreviewed Ampere patch");
}
source = source.replace(buildOptionsPattern, optionsAddition + buildOptionsMatch[0]);

const cpuFallbackPattern = /return await loadLlama\(\s*false,\s*false\s*\);/;
if (!cpuFallbackPattern.test(source)) {
  throw new Error("QMD CPU fallback changed; refusing to apply an unreviewed Ampere patch");
}
source = source.replace(cpuFallbackPattern, "return await loadLlama(false, useAmpereNativeBuild ? canBuild : false);");

fs.writeFileSync(file, source);
NODE
