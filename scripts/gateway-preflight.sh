#!/usr/bin/env bash
set -Eeuo pipefail

repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
hermes_home=${HERMES_HOME:-$HOME/.hermes}
env_file="$hermes_home/profiles/orchestrator/.env"

[[ -f $env_file ]] || { echo "Gateway secret file is missing: $env_file" >&2; exit 1; }
[[ $(stat -c '%a' "$env_file") == 600 ]] || { echo "$env_file must have mode 0600." >&2; exit 1; }

dotenv_value() {
  local key=$1
  sed -n "s/^${key}=//p" "$env_file" | tail -n 1 | tr -d '\r'
}

token=$(dotenv_value TELEGRAM_BOT_TOKEN)
operator=$(dotenv_value TELEGRAM_ALLOWED_USERS)
allowed_chat=$(dotenv_value TELEGRAM_ALLOWED_CHATS)

[[ $token =~ ^[0-9]+:[A-Za-z0-9_-]{20,}$ ]] || {
  echo "Set a valid TELEGRAM_BOT_TOKEN in $env_file." >&2
  exit 1
}
[[ $operator =~ ^[0-9]+$ ]] || {
  echo "TELEGRAM_ALLOWED_USERS must contain exactly one numeric operator ID." >&2
  exit 1
}
[[ $allowed_chat == "$operator" ]] || {
  echo "TELEGRAM_ALLOWED_CHATS must equal the operator ID to enforce DM-only access." >&2
  exit 1
}

for key in TELEGRAM_ALLOW_ALL_USERS TELEGRAM_GUEST_MODE GATEWAY_ALLOW_ALL_USERS; do
  [[ $(dotenv_value "$key") == false ]] || { echo "$key must be false." >&2; exit 1; }
done
for key in TELEGRAM_GROUP_ALLOWED_USERS TELEGRAM_GROUP_ALLOWED_CHATS; do
  [[ -z $(dotenv_value "$key") ]] || { echo "$key must remain empty for DM-only access." >&2; exit 1; }
done

if grep -Eq '^OPENAI_API_KEY=.+$' "$env_file" "$hermes_home"/profiles/*/.env 2>/dev/null; then
  echo "OPENAI_API_KEY is forbidden in this OAuth-only deployment." >&2
  exit 1
fi
for profile_env in "$hermes_home"/profiles/*/.env; do
  [[ -e $profile_env && $profile_env != "$env_file" ]] || continue
  if grep -q '^TELEGRAM_' "$profile_env"; then
    echo "Telegram credentials or policy appeared in a secondary profile: $profile_env" >&2
    exit 1
  fi
done

"$repo_root/scripts/verify-lcm-pin.sh"
"$repo_root/scripts/verify-qmd-pin.sh"
"$repo_root/scripts/verify-langfuse-pin.sh"

for profile in orchestrator researcher coder reviewer web-monitor; do
  profile_env="$hermes_home/profiles/$profile/.env"
  [[ -f $profile_env ]] || { echo "Missing profile environment: $profile_env" >&2; exit 1; }
  profile_value() {
    local key=$1
    sed -n "s/^${key}=//p" "$profile_env" | tail -n 1 | tr -d '\r'
  }
  [[ $(profile_value HERMES_LANGFUSE_PUBLIC_KEY) =~ ^pk-lf- ]] || { echo "$profile Langfuse public key is invalid." >&2; exit 1; }
  [[ $(profile_value HERMES_LANGFUSE_SECRET_KEY) =~ ^sk-lf- ]] || { echo "$profile Langfuse secret key is invalid." >&2; exit 1; }
  [[ $(profile_value HERMES_LANGFUSE_BASE_URL) =~ ^https://[^[:space:]]+$ ]] || { echo "$profile Langfuse endpoint must use HTTPS." >&2; exit 1; }
  [[ $(profile_value HERMES_LANGFUSE_CAPTURE) == metadata ]] || { echo "$profile Langfuse capture must be metadata." >&2; exit 1; }
  [[ $(profile_value HERMES_LANGFUSE_ENV) == production-$profile ]] || { echo "$profile Langfuse environment label is invalid." >&2; exit 1; }
  [[ $(profile_value HERMES_LANGFUSE_RELEASE) == v2026.9.11 ]] || { echo "$profile Langfuse release is invalid." >&2; exit 1; }
  hermes -p "$profile" config check >/dev/null
done

echo "Gateway preflight passed: one operator, one DM chat, no group access, no OpenAI API key, reviewed local plugins and Langfuse SDK."
