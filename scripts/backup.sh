#!/usr/bin/env bash
set -Eeuo pipefail

repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
hermes_home=${HERMES_HOME:-$HOME/.hermes}
backup_root=${BACKUP_ROOT:-$HOME/hermes-backups}
timestamp=$(date -u +%Y%m%dT%H%M%SZ)
archive="$backup_root/hermes-state-$timestamp.tar.gz"
stage=$(mktemp -d "${TMPDIR:-/tmp}/hermes-backup.XXXXXX")
gateway_was_active=0
dashboard_was_active=0

cleanup() {
  local status=$?
  case "$stage" in
    "${TMPDIR:-/tmp}"/hermes-backup.*) rm -rf -- "$stage" ;;
    *) echo "Refusing to remove unexpected staging path: $stage" >&2 ;;
  esac
  if (( gateway_was_active )); then
    systemctl --user start hermes-gateway.service || true
  fi
  if (( dashboard_was_active )); then
    systemctl --user start hermes-dashboard.service || true
  fi
  if (( status != 0 )); then
    rm -f -- "$archive.tmp"
  fi
  exit "$status"
}
trap cleanup EXIT

[[ -d $hermes_home ]] || { echo "Hermes home does not exist: $hermes_home" >&2; exit 1; }
[[ -d /srv/hermes/projects && -d /srv/hermes/wiki ]] || {
  echo "/srv/hermes/projects and /srv/hermes/wiki must exist." >&2
  exit 1
}
mkdir -p "$backup_root"
chmod 0700 "$backup_root"

source_kib=0
for source_path in "$hermes_home" /srv/hermes/projects /srv/hermes/wiki /srv/hermes/artifacts; do
  source_kib=$((source_kib + $(du -sk -- "$source_path" | awk '{print $1}')))
done
required_kib=$((source_kib * 2))
backup_available_kib=$(df -Pk "$backup_root" | awk 'NR==2 {print $4}')
stage_available_kib=$(df -Pk "${TMPDIR:-/tmp}" | awk 'NR==2 {print $4}')
if (( backup_available_kib < required_kib || stage_available_kib < source_kib )); then
  echo "Insufficient free space for a consistent backup (need ${required_kib} KiB at $backup_root and ${source_kib} KiB at ${TMPDIR:-/tmp})." >&2
  exit 1
fi

if systemctl --user is-active --quiet hermes-dashboard.service; then
  dashboard_was_active=1
  systemctl --user stop hermes-dashboard.service
fi
if systemctl --user is-active --quiet hermes-gateway.service; then
  gateway_was_active=1
  systemctl --user stop hermes-gateway.service
fi

mkdir -p "$stage/home" "$stage/srv/hermes" "$stage/deployment/infra"
cp -a -- "$hermes_home" "$stage/home/.hermes"
cp -a -- /srv/hermes/projects "$stage/srv/hermes/projects"
cp -a -- /srv/hermes/wiki "$stage/srv/hermes/wiki"
cp -a -- /srv/hermes/artifacts "$stage/srv/hermes/artifacts"

# Hermes itself, its managed Node runtime, QMD runtime, and browser link are
# reproducible from this reviewed bundle. Keep profile state and LCM intact.
for rebuildable in hermes-agent node qmd-runtime bin; do
  rm -rf -- "$stage/home/.hermes/$rebuildable"
done

for state_file in infra/.env infra/images.lock.env; do
  if [[ -f "$repo_root/$state_file" ]]; then
    cp -p -- "$repo_root/$state_file" "$stage/deployment/infra/"
  fi
done

{
  printf 'created_utc=%s\n' "$timestamp"
  printf 'hostname=%s\n' "$(hostname)"
  printf 'hermes_version=%s\n' "$(hermes --version 2>&1 || printf unknown)"
  printf 'scope=profile state,/srv/hermes/projects,/srv/hermes/wiki,/srv/hermes/artifacts,infra runtime state\n'
  printf 'excluded_rebuildable=hermes-agent,node,qmd-runtime,bin\n'
} > "$stage/MANIFEST.txt"

tar --acls --xattrs --numeric-owner -C "$stage" -czf "$archive.tmp" .
chmod 0600 "$archive.tmp"
mv -f -- "$archive.tmp" "$archive"
(cd -- "$backup_root" && sha256sum "$(basename -- "$archive")" > "$(basename -- "$archive.sha256")")
chmod 0600 "$archive.sha256"

echo "Backup created: $archive"
echo "The archive contains credentials. Copy it off-host using an encrypted channel."
