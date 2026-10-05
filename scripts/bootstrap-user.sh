#!/usr/bin/env bash
set -Eeuo pipefail

repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
hermes_home=${HERMES_HOME:-$HOME/.hermes}
sandbox_tag=hermes-sandbox:2026.09.11
expected_profiles=(orchestrator researcher coder reviewer wiki-maintainer web-scraper web-monitor)

# A checkout prepared on Windows may not retain POSIX executable bits. From
# this point onward all installed helper scripts can be invoked directly.
chmod 0755 "$repo_root"/scripts/*.sh

[[ $EUID -ne 0 ]] || { echo "Run this as the dedicated unprivileged Hermes user." >&2; exit 1; }
[[ $hermes_home == "$HOME/.hermes" ]] || {
  echo "This hardened systemd bundle requires HERMES_HOME=$HOME/.hermes." >&2
  exit 1
}
expected_home=$(getent passwd "$(id -un)" | cut -d: -f6)
[[ $HOME == "$expected_home" ]] || {
  echo "HOME=$HOME does not match the login home for $(id -un): $expected_home" >&2
  echo "Log in directly as the dedicated Hermes user; do not run bootstrap through sudo -u or su without a login shell." >&2
  exit 1
}
user_runtime_dir="/run/user/$(id -u)"
export XDG_RUNTIME_DIR="$user_runtime_dir"
export DBUS_SESSION_BUS_ADDRESS="unix:path=$user_runtime_dir/bus"
if [[ ! -S $user_runtime_dir/bus ]] || ! systemctl --user show-environment >/dev/null 2>&1; then
  echo "The systemd user bus is unavailable for $(id -un) at $user_runtime_dir/bus." >&2
  echo "Run scripts/install-host.sh as root if needed, then log in directly as $(id -un) and retry." >&2
  exit 1
fi

# SSH login shells do not always receive the address of the existing user bus.
# Keep systemctl --user usable after login and after a host reboot.
if ! grep -Fq '# Hermes deployment: systemd user bus' "$HOME/.bashrc" 2>/dev/null; then
  cat >> "$HOME/.bashrc" <<'EOF'

# Hermes deployment: systemd user bus
if [ -S "/run/user/$(id -u)/bus" ]; then
    export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
    export DBUS_SESSION_BUS_ADDRESS="unix:path=$XDG_RUNTIME_DIR/bus"
fi
EOF
fi
[[ $(uname -m) == aarch64 || $(uname -m) == arm64 ]] || { echo "ARM64 is required." >&2; exit 1; }
[[ -e /sys/fs/cgroup/cgroup.controllers ]] || { echo "cgroup v2 is required." >&2; exit 1; }
# shellcheck disable=SC1091
source /etc/os-release
case "${ID:-}:${VERSION_ID:-}" in
  ubuntu:22.04|ubuntu:24.04|debian:12) ;;
  *) echo "Supported hosts are Ubuntu 22.04/24.04 and Debian 12." >&2; exit 1 ;;
esac

memory_kib=$(awk '/MemTotal:/ {print $2}' /proc/meminfo)
(( memory_kib >= 10 * 1024 * 1024 )) || { echo "At least 10 GiB RAM is required." >&2; exit 1; }
free_kib=$(df -Pk "$HOME" | awk 'NR==2 {print $4}')
(( free_kib >= 20 * 1024 * 1024 )) || { echo "At least 20 GiB free disk is required." >&2; exit 1; }
srv_free_kib=$(df -Pk /srv/hermes | awk 'NR==2 {print $4}')
(( srv_free_kib >= 20 * 1024 * 1024 )) || { echo "At least 20 GiB free disk is required on /srv/hermes." >&2; exit 1; }

command -v docker >/dev/null 2>&1 || { echo "docker is required" >&2; exit 1; }
command -v git >/dev/null 2>&1 || { echo "git is required" >&2; exit 1; }
"$repo_root/scripts/install-hermes.sh"
export PATH="$HOME/.hermes/bin:$HOME/.local/bin:$PATH"
command -v hermes >/dev/null 2>&1 || { echo "Hermes installation did not create ~/.local/bin/hermes." >&2; exit 1; }
"$repo_root/scripts/verify-hermes-pin.sh"

export DOCKER_HOST=${DOCKER_HOST:-unix:///run/user/$(id -u)/docker.sock}
docker info >/dev/null
docker info --format '{{json .SecurityOptions}}' | grep -qi rootless || {
  echo "The active Docker daemon is not rootless: $DOCKER_HOST" >&2
  exit 1
}
[[ $(docker info --format '{{.CgroupVersion}}') == 2 ]] || {
  echo "The rootless Docker daemon is not enforcing cgroup v2." >&2
  exit 1
}
docker_warnings=$(docker info --format '{{json .Warnings}}')
if grep -Eqi 'no (memory limit|cpu cfs quota) support' <<<"$docker_warnings"; then
  echo "Rootless Docker cannot enforce the required CPU/memory limits." >&2
  exit 1
fi

version_text=$(hermes --version 2>&1 || true)
approved_tag=${APPROVED_HERMES_TAG:-v2026.9.11}
if [[ $approved_tag == v2026.9.11 && $version_text != *"v2026.9.11"* && $version_text != *"0.21.2"* ]]; then
  echo "Expected Hermes v2026.9.11 / 0.21.2; found: $version_text" >&2
  exit 1
fi

install -d -m 0750 /srv/hermes/monitor /srv/hermes/monitor/monitoring
for path in /srv/hermes/projects /srv/hermes/wiki /srv/hermes/monitor /srv/hermes/artifacts; do
  [[ -d $path && -w $path ]] || { echo "$path must exist and be writable by $(id -un)." >&2; exit 1; }
done

if [[ ! -e /srv/hermes/monitor/.hermes-monitor-workspace ]]; then
  printf 'Hermes Web Monitor workspace\n' > /srv/hermes/monitor/.hermes-monitor-workspace
fi

if [[ ! -d /srv/hermes/wiki/.git ]]; then
  git -C /srv/hermes/wiki init
  git -C /srv/hermes/wiki config user.name "Hermes Wiki Maintainer"
  git -C /srv/hermes/wiki config user.email "hermes-wiki@localhost"
fi
wiki_lock=/srv/hermes/wiki/.hermes-maintenance/wiki-writer.lock
if [[ -e $wiki_lock && ! -d $wiki_lock ]]; then
  [[ -f $wiki_lock && ! -s $wiki_lock ]] || {
    echo "Refusing to replace a non-directory wiki writer lock: $wiki_lock" >&2
    exit 1
  }
  rm -f -- "$wiki_lock"
fi
install -d -m 0750 /srv/hermes/wiki/.hermes-maintenance
install -m 0644 "$repo_root/scripts/wiki-writer-lock.py" \
  /srv/hermes/wiki/.hermes-maintenance/wiki-writer-lock.py
wiki_git_excludes=/srv/hermes/wiki/.git/info/exclude
touch "$wiki_git_excludes"
grep -Fxq '/.hermes-maintenance/' "$wiki_git_excludes" ||
  printf '%s\n' '/.hermes-maintenance/' >> "$wiki_git_excludes"

mkdir -p "$hermes_home"
timestamp=$(date -u +%Y%m%dT%H%M%SZ)

install_profile_files() {
  local name=$1
  local destination="$hermes_home/profiles/$name" source="$repo_root/profiles/$name"
  mkdir -p "$destination"
  for filename in config.yaml SOUL.md SKILLS.md; do
    [[ -f "$source/$filename" ]] || continue
    if [[ -f "$destination/$filename" ]] && ! cmp -s "$source/$filename" "$destination/$filename"; then
      cp -p -- "$destination/$filename" "$destination/${filename}.pre-hermes-deployment.${timestamp}"
    fi
    install -m 0644 "$source/$filename" "$destination/$filename"
  done
  if [[ -d "$source/skills" ]]; then
    if [[ -d "$destination/skills" ]]; then
      mv -- "$destination/skills" "$destination/skills.pre-hermes-deployment.${timestamp}"
    fi
    cp -a -- "$source/skills" "$destination/skills"
  fi
  local shared_skill_source="$repo_root/profiles/shared/skills/asd-ste100"
  local shared_skill_destination="$destination/skills/asd-ste100"
  if [[ -d "$shared_skill_source" ]]; then
    mkdir -p "$destination/skills"
    if [[ -e "$shared_skill_destination" ]] \
      && ! diff -qr -- "$shared_skill_source" "$shared_skill_destination" >/dev/null; then
      mv -- "$shared_skill_destination" \
        "$shared_skill_destination.pre-hermes-deployment.${timestamp}"
    fi
    if [[ ! -e "$shared_skill_destination" ]]; then
      cp -a -- "$shared_skill_source" "$shared_skill_destination"
    fi
  fi
  if [[ ! -e "$destination/.env" ]]; then
    install -m 0600 "$repo_root/profiles/$name/.env.example" "$destination/.env"
  else
    chmod 0600 "$destination/.env"
  fi
  if [[ $name == researcher || $name == web-scraper || $name == web-monitor ]]; then
    if grep -q '^AGENT_BROWSER_EXECUTABLE_PATH=' "$destination/.env"; then
      sed -i "s|^AGENT_BROWSER_EXECUTABLE_PATH=.*|AGENT_BROWSER_EXECUTABLE_PATH=$hermes_home/bin/chromium|" \
        "$destination/.env"
    else
      printf '\nAGENT_BROWSER_EXECUTABLE_PATH=%s\n' "$hermes_home/bin/chromium" >> "$destination/.env"
    fi
  fi
}

declare -A descriptions=(
  [orchestrator]="Routes work through durable Kanban cards and enforces review, isolation, and the human publishing gate."
  [researcher]="Finds and evaluates primary sources, producing cited evidence reports without changing application code."
  [coder]="Implements scoped code changes in isolated Git worktrees, verifies them, and requests independent review."
  [reviewer]="Independently reviews diffs and verification evidence, approving or returning work without editing it."
  [wiki-maintainer]="Maintains the local wiki vault, provenance, links, indexes, and reviewed research summaries."
  [web-scraper]="Performs bounded public-web extraction into structured, provenance-rich task artifacts."
  [web-monitor]="Runs scheduled page comparisons in a paused state and reports only material changes."
)

for profile in "${expected_profiles[@]}"; do
  if [[ ! -d "$hermes_home/profiles/$profile" ]]; then
    hermes profile create "$profile" --description "${descriptions[$profile]}" --no-alias --no-skills
  fi
  install_profile_files "$profile"
  if [[ $profile == coder ]]; then
    "$repo_root/scripts/install-lcm.sh"
  fi
  hermes -p "$profile" skills opt-out
  hermes profile describe "$profile" --text "${descriptions[$profile]}"
done

"$repo_root/scripts/install-qmd.sh"
"$repo_root/scripts/install-langfuse.sh"

"$repo_root/scripts/sync-boards.sh"

infra_env="$repo_root/infra/.env"
if [[ ! -e $infra_env ]]; then
  umask 077
  searx_secret=$(openssl rand -hex 32)
  postgres_password=$(openssl rand -hex 32)
  bull_key=$(openssl rand -hex 32)
  {
    printf 'SEARXNG_SECRET=%s\n' "$searx_secret"
    printf 'POSTGRES_USER=firecrawl\n'
    printf 'POSTGRES_PASSWORD=%s\n' "$postgres_password"
    printf 'POSTGRES_DB=firecrawl\n'
    printf 'BULL_AUTH_KEY=%s\n' "$bull_key"
    printf 'TZ=Europe/Belgrade\n'
  } > "$infra_env"
fi
chmod 0600 "$infra_env"

"$repo_root/scripts/verify-images.sh"
# shellcheck disable=SC1091
source "$repo_root/infra/images.lock.env"
docker build --platform linux/arm64 --build-arg BASE_IMAGE="$SANDBOX_BASE_IMAGE" \
  -t "$sandbox_tag" "$repo_root/images/hermes-sandbox"

hermes_bin="$hermes_home/hermes-agent/venv/bin/hermes"
[[ -x $hermes_bin ]] || { echo "Managed Hermes launcher is missing: $hermes_bin" >&2; exit 1; }

# Let Hermes generate its native gateway unit. Keep deployment policy in a
# drop-in so `hermes gateway status/restart` recognizes the service.
unit_dir="$HOME/.config/systemd/user"
# Install the native default gateway without copying or modifying the built-in
# default profile files or its .env.
"$hermes_bin" gateway install --force --no-start-now
gateway_service=hermes-gateway.service
escaped_root=${repo_root//&/\\&}
escaped_root=${escaped_root//\//\\/}
default_dropin="$unit_dir/${gateway_service}.d"
mkdir -p "$default_dropin"
sed -e "s/@DEPLOY_DIR@/${escaped_root}/g" \
  "$repo_root/systemd/hermes-gateway.service.d/override.conf.in" \
  > "$default_dropin/override.conf"
# Install the second native profile unit. Hermes currently emits the profile
# home in HERMES_HOME and also emits --profile, which double-prefixes the
# profile path at runtime. Normalize the unit to the root home; --profile then
# selects the orchestrator secrets and configuration.
"$hermes_bin" -p orchestrator gateway install --force --no-start-now
orchestrator_service=hermes-gateway-orchestrator.service
orchestrator_unit="$unit_dir/$orchestrator_service"
sed -i \
  -e "s|^WorkingDirectory=.*|WorkingDirectory=$hermes_home|" \
  -e "s|^Environment=\"HERMES_HOME=.*\"|Environment=\"HERMES_HOME=$hermes_home\"|" \
  -e 's| gateway run$| gateway run --force --external-supervisor|' \
  "$orchestrator_unit"
orchestrator_dropin="$unit_dir/${orchestrator_service}.d"
mkdir -p "$orchestrator_dropin"
sed -e "s/@DEPLOY_DIR@/${escaped_root}/g" \
  "$repo_root/systemd/hermes-gateway-orchestrator.service.d/override.conf.in" \
  > "$orchestrator_dropin/override.conf"
for unit in \
  hermes-web.service \
  hermes-dashboard.service \
  hermes-qmd-index.service \
  hermes-qmd-index.timer \
  hermes-qmd-embed.service \
  hermes-qmd-embed.timer; do
  sed -e "s/@DEPLOY_DIR@/${escaped_root}/g" \
    "$repo_root/systemd/${unit}.in" > "$unit_dir/$unit"
done
systemctl --user daemon-reload

for profile in "${expected_profiles[@]}"; do
  hermes -p "$profile" config check
done

cat <<EOF
Bootstrap complete. Services were installed but not started.

Next:
  1. Fill ~/.hermes/profiles/orchestrator/.env with TELEGRAM_BOT_TOKEN and set both Telegram ID fields to your numeric user ID.
  2. Add OPENROUTER_API_KEY only to fallback-enabled profile .env files.
  3. Fill the Langfuse key and HTTPS endpoint fields in Langfuse-enabled profile .env files; capture mode is metadata-only and validation requires them.
  4. Run: hermes auth add openai-codex
  5. Enable hermes-web, hermes-gateway, hermes-dashboard, the QMD index timer, and the QMD embed timer.
  6. Install the paused wiki triage job: $repo_root/scripts/install-wiki-triage.sh
  7. Run: $repo_root/scripts/validate.sh
EOF
