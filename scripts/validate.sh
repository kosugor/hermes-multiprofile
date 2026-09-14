#!/usr/bin/env bash
set -Eeuo pipefail

repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
hermes_home=${HERMES_HOME:-$HOME/.hermes}
sandbox_image=hermes-sandbox:2026.09.11
soak_hours=0
online=1
failures=0
export PATH="$hermes_home/node/bin:$HOME/.local/bin:$PATH"
export AGENT_BROWSER_EXECUTABLE_PATH="$hermes_home/bin/chromium"

usage() {
  echo "Usage: $0 [--offline] [--soak-hours N | --no-soak]" >&2
}

while (($#)); do
  case "$1" in
    --offline) online=0; shift ;;
    --soak-hours)
      [[ $# -ge 2 && $2 =~ ^[0-9]+$ ]] || { usage; exit 2; }
      soak_hours=$2
      shift 2
      ;;
    --no-soak) soak_hours=0; shift ;;
    -h|--help) usage; exit 0 ;;
    *) usage; exit 2 ;;
  esac
done

pass() { printf 'PASS  %s\n' "$*"; }
fail() { printf 'FAIL  %s\n' "$*" >&2; failures=$((failures + 1)); }

run_check() {
  local label=$1
  shift
  if "$@" >/dev/null 2>&1; then pass "$label"; else fail "$label"; fi
}

[[ $EUID -ne 0 ]] || { echo "Run as the unprivileged Hermes user." >&2; exit 1; }
[[ $(uname -m) == aarch64 || $(uname -m) == arm64 ]] || fail "host architecture is ARM64"
[[ -e /sys/fs/cgroup/cgroup.controllers ]] && pass "cgroup v2 is active" || fail "cgroup v2 is active"

for command_name in hermes agent-browser playwright docker jq curl ss nft; do
  command -v "$command_name" >/dev/null 2>&1 && pass "$command_name is installed" || fail "$command_name is installed"
done
(( failures == 0 )) || { echo "Required commands or host features are missing." >&2; exit 1; }

[[ $(agent-browser --version 2>/dev/null || true) == *"0.26.0"* ]] \
  && pass "agent-browser is pinned to 0.26.0" || fail "agent-browser is pinned to 0.26.0"
[[ $(playwright --version 2>/dev/null || true) == *"1.62.1"* ]] \
  && pass "Playwright is pinned to 1.62.1" || fail "Playwright is pinned to 1.62.1"
[[ -L $hermes_home/bin/chromium && -x $hermes_home/bin/chromium ]] \
  && pass "ARM64 Playwright Chromium is installed" || fail "ARM64 Playwright Chromium is installed"
grep -Fxq "AGENT_BROWSER_EXECUTABLE_PATH=$hermes_home/bin/chromium" \
  "$hermes_home/profiles/researcher/.env" 2>/dev/null \
  && pass "Researcher uses the managed Chromium path" || fail "Researcher uses the managed Chromium path"

export DOCKER_HOST=${DOCKER_HOST:-unix:///run/user/$(id -u)/docker.sock}
if docker info --format '{{json .SecurityOptions}}' 2>/dev/null | grep -qi rootless; then
  pass "Docker daemon is rootless"
else
  fail "Docker daemon is rootless ($DOCKER_HOST)"
fi
[[ $(docker info --format '{{.CgroupVersion}}' 2>/dev/null || true) == 2 ]] \
  && pass "rootless Docker uses cgroup v2" || fail "rootless Docker uses cgroup v2"
docker_warnings=$(docker info --format '{{json .Warnings}}' 2>/dev/null || true)
if grep -Eqi 'no (memory limit|cpu cfs quota) support' <<<"$docker_warnings"; then
  fail "rootless Docker enforces CPU and memory limits"
else
  pass "rootless Docker enforces CPU and memory limits"
fi

expected=(default researcher coder reviewer wiki-maintainer web-scraper web-monitor)
actual_profile_dirs=(default)
while IFS= read -r name; do actual_profile_dirs+=("$name"); done < <(
  find "$hermes_home/profiles" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' 2>/dev/null | sort
)
if [[ ${#actual_profile_dirs[@]} -eq 7 ]]; then
  pass "exactly seven profile directories are installed"
else
  fail "exactly seven profile directories are installed (found ${#actual_profile_dirs[@]})"
fi

profile_listing=$(hermes profile list 2>&1 || true)
for profile in "${expected[@]}"; do
  if [[ $profile == default ]]; then
    grep -q 'Orchestrator' <<<"$profile_listing" && pass "default displays as Orchestrator" || fail "default displays as Orchestrator"
  else
    grep -q "$profile" <<<"$profile_listing" && pass "profile exists: $profile" || fail "profile exists: $profile"
  fi
done

for profile in "${expected[@]}"; do
  if [[ $profile == default ]]; then
    run_check "config check: default" hermes config check
  else
    run_check "config check: $profile" hermes -p "$profile" config check
  fi
done
run_check "Hermes checkout is clean and pinned" "$repo_root/scripts/verify-hermes-pin.sh"

hermes_script=$(readlink -f -- "$(command -v hermes)")
hermes_python=$(sed -n '1s/^#!//p' "$hermes_script")
if [[ -x $hermes_python ]]; then
  run_check "resolved tool inventories match the reviewed allowlist" \
    "$hermes_python" "$repo_root/scripts/audit-tools.py" --bundle "$repo_root"
else
  fail "could not resolve Hermes managed Python for tool inventory audit"
fi

run_check "Compose resolves only locked image variables" "$repo_root/scripts/compose.sh" config
running_output=$("$repo_root/scripts/compose.sh" ps --status running -q 2>/dev/null || true)
running_count=$(grep -c . <<<"$running_output" || true)
[[ $running_count -eq 7 ]] && pass "all seven web-stack containers are running" || fail "all seven web-stack containers are running (found $running_count)"

run_check "gateway systemd service is active" systemctl --user is-active --quiet hermes-gateway.service
run_check "dashboard systemd service is active" systemctl --user is-active --quiet hermes-dashboard.service
run_check "web systemd service is active" systemctl --user is-active --quiet hermes-web.service

unexpected_listeners=$(ss -H -lnt | awk '
  $4 ~ /:(3002|8888|9119)$/ && $4 !~ /^127\.0\.0\.1:/ && $4 !~ /^\[::1\]:/ { print }
')
[[ -z $unexpected_listeners ]] && pass "dashboard and web APIs have no public listeners" || {
  fail "dashboard and web APIs have no public listeners"
  printf '%s\n' "$unexpected_listeners" >&2
}

searx_response=$(curl --fail --silent --show-error --max-time 30 \
  'http://127.0.0.1:8888/search?q=hermes+agent&format=json' 2>/dev/null || true)
jq -e '.results | type == "array"' <<<"$searx_response" >/dev/null 2>&1 \
  && pass "SearXNG JSON endpoint works" || fail "SearXNG JSON endpoint works"

firecrawl_health=$(curl --fail --silent --show-error --max-time 20 \
  'http://127.0.0.1:3002/v0/health/liveness' 2>/dev/null || true)
[[ -n $firecrawl_health ]] && pass "Firecrawl liveness endpoint works" || fail "Firecrawl liveness endpoint works"

if (( online )); then
  scrape() {
    local label=$1 url=$2 response
    response=$(curl --fail --silent --show-error --max-time 120 \
      -H 'Authorization: Bearer self-hosted' -H 'Content-Type: application/json' \
      --data "{\"url\":\"$url\",\"formats\":[\"markdown\"]}" \
      'http://127.0.0.1:3002/v1/scrape' 2>/dev/null || true)
    jq -e '.success == true and (.data.markdown | type == "string")' <<<"$response" >/dev/null 2>&1 \
      && pass "$label" || fail "$label"
  }
  scrape "Firecrawl extracts a static public page" 'https://example.com/'
  scrape "Firecrawl extracts a JavaScript-rendered public page" 'https://quotes.toscrape.com/js/'

  browser_session="hermes-validation-$$"
  browser_title=
  if timeout 150 agent-browser --session "$browser_session" open 'https://example.com/' >/dev/null 2>&1 \
    && browser_title=$(timeout 30 agent-browser --session "$browser_session" get title 2>/dev/null) \
    && grep -q 'Example Domain' <<<"$browser_title"; then
    pass "local headless browser opens a public page"
  else
    fail "local headless browser opens a public page"
  fi
  timeout 30 agent-browser --session "$browser_session" close >/dev/null 2>&1 || true
fi

for blocked_url in \
  'http://169.254.169.254/latest/meta-data/' \
  'http://2852039166/latest/meta-data/' \
  'http://[::ffff:169.254.169.254]/latest/meta-data/' \
  'https://httpbin.org/redirect-to?url=http%3A%2F%2F169.254.169.254%2Flatest%2Fmeta-data%2F' \
  'http://127.0.0.1:8888/' \
  'http://10.0.0.1/'; do
  response=$(curl --silent --show-error --max-time 20 \
    -H 'Authorization: Bearer self-hosted' -H 'Content-Type: application/json' \
    --data "{\"url\":\"$blocked_url\",\"formats\":[\"markdown\"]}" \
    'http://127.0.0.1:3002/v1/scrape' 2>/dev/null || true)
  if [[ -z $response ]] || ! jq -e 'type == "object" and has("success")' <<<"$response" >/dev/null 2>&1; then
    fail "Firecrawl returns an explicit denial for private target: $blocked_url"
  elif jq -e '.success == true' <<<"$response" >/dev/null 2>&1; then
    fail "Firecrawl rejects private target: $blocked_url"
  else
    pass "Firecrawl rejects private target: $blocked_url"
  fi
done

egress_file=/etc/nftables.d/hermes-egress.nft
if systemctl is-active --quiet nftables.service \
  && [[ -r $egress_file ]] \
  && grep -q "meta skuid $(id -u)" "$egress_file"; then
  pass "UID-scoped egress nftables service and policy are installed"
else
  fail "UID-scoped egress nftables service and policy are installed"
fi

canary=$(mktemp -d /srv/hermes/artifacts/sandbox-canary.XXXXXX)
host_marker="$HOME/.hermes-sandbox-host-canary.$$.secret"
printf 'host-only-sentinel\n' > "$host_marker"
chmod 0600 "$host_marker"
cleanup_canary() {
  case "$canary" in /srv/hermes/artifacts/sandbox-canary.*) rm -rf -- "$canary" ;; esac
  rm -f -- "$host_marker"
}
trap cleanup_canary EXIT
chmod 0700 "$canary"
if docker run --rm --network none --cpus 1 --memory 1536m --pids-limit 256 \
  --user "$(id -u):$(id -g)" --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=128m \
  --tmpfs /home/hermes:rw,noexec,nosuid,size=64m \
  -e "HOST_MARKER=$host_marker" \
  -v "$canary:/workspace:rw" -w /workspace "$sandbox_image" \
  bash -ceu '
    touch /workspace/writable
    test ! -S /var/run/docker.sock
    test ! -e /host
    test ! -e /root/.ssh
    test ! -e "$HOST_MARKER"
    ! curl --silent --max-time 3 https://example.com/ >/dev/null
  '; then
  pass "sandbox can only write its workspace and has no network/socket/host secrets"
else
  fail "sandbox can only write its workspace and has no network/socket/host secrets"
fi

if (( soak_hours > 0 )); then
  echo "Starting ${soak_hours}-hour resource soak; this process must remain attached."
  deadline=$(( $(date +%s) + soak_hours * 3600 ))
  high_load_streak=0
  sustained_load_failure=0
  while (( $(date +%s) < deadline )); do
    memory_kib=$(awk '/MemTotal:/ {total=$2} /MemAvailable:/ {available=$2} END {print total-available}' /proc/meminfo)
    (( memory_kib < 10 * 1024 * 1024 )) || fail "soak memory remains below 10 GiB"
    oom_count=$(journalctl -k --since '-2 minutes' --no-pager 2>/dev/null | grep -Eci 'oom-kill|out of memory' || true)
    (( oom_count == 0 )) || fail "soak has no OOM kills"
    load_one=$(cut -d' ' -f1 /proc/loadavg)
    if awk -v load="$load_one" 'BEGIN {exit !(load > 2.0)}'; then
      high_load_streak=$((high_load_streak + 1))
    else
      high_load_streak=0
    fi
    if (( high_load_streak >= 5 && sustained_load_failure == 0 )); then
      fail "soak has no sustained five-minute load above two cores"
      sustained_load_failure=1
    fi
    sleep 60
  done
  (( sustained_load_failure == 0 )) && pass "soak has no sustained five-minute load above two cores"
fi

cleanup_canary
trap - EXIT

if (( failures > 0 )); then
  echo "$failures validation check(s) failed." >&2
  exit 1
fi
echo "All automated validation checks passed."
echo "Complete the Kanban request-changes fixture, Telegram denial test, and monitor delivery fixture from docs/acceptance.md."
