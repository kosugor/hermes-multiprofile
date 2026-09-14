#!/usr/bin/env bash
set -Eeuo pipefail

repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
apply=0

usage() {
  echo "Usage: $0 [--plan | --apply]" >&2
}

while (($#)); do
  case "$1" in
    --plan) apply=0; shift ;;
    --apply) apply=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) usage; exit 2 ;;
  esac
done

echo "Service image sources to resolve for linux/arm64:"
sed -n 's/_SOURCE=/: /p' "$repo_root/infra/images.sources.env"

if (( apply == 0 )); then
  cat <<EOF

Plan only. Before --apply, review infra/images.sources.env and the upstream
release notes. This refreshes service image locks, not the Hermes installation.
EOF
  exit 0
fi

lock_file="$repo_root/infra/images.lock.env"
[[ -f $lock_file ]] || { echo "Missing $lock_file; run bootstrap first." >&2; exit 1; }
old_lock=$(mktemp "${TMPDIR:-/tmp}/hermes-images-lock.XXXXXX")
cp -p -- "$lock_file" "$old_lock"
rollback() {
  local status=$?
  if (( status != 0 )); then
    echo "Upgrade failed; restoring the previous image lock and web stack." >&2
    cp -p -- "$old_lock" "$lock_file"
    systemctl --user restart hermes-web.service || true
  fi
  rm -f -- "$old_lock"
  exit "$status"
}
trap rollback EXIT

"$repo_root/scripts/backup.sh"
"$repo_root/scripts/lock-images.sh"
"$repo_root/scripts/compose.sh" config >/dev/null
systemctl --user restart hermes-web.service
"$repo_root/scripts/validate.sh" --no-soak
trap - EXIT
rm -f -- "$old_lock"

cat <<'EOF'
Web-service upgrade validated. Review and commit infra/images.lock.env. Hermes
itself remains pinned; use scripts/upgrade-hermes.sh for a separately reviewed
exact release tag.
EOF
