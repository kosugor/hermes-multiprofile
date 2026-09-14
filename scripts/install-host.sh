#!/usr/bin/env bash
set -Eeuo pipefail

usage() {
  echo "Usage: sudo $0 [--user USER]" >&2
}

target_user=hermes
while (($#)); do
  case "$1" in
    --user)
      [[ $# -ge 2 ]] || { usage; exit 2; }
      target_user=$2
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      usage
      exit 2
      ;;
  esac
done

[[ $EUID -eq 0 ]] || { echo "Run this script as root." >&2; exit 1; }
[[ $target_user =~ ^[a-z_][a-z0-9_-]*$ ]] || { echo "Invalid user name." >&2; exit 1; }

arch=$(dpkg --print-architecture 2>/dev/null || true)
[[ $arch == arm64 ]] || { echo "This deployment requires Debian/Ubuntu arm64; found '$arch'." >&2; exit 1; }

# shellcheck disable=SC1091
source /etc/os-release
case "${ID:-}" in
  ubuntu)
    [[ ${VERSION_ID:-} == 22.04 || ${VERSION_ID:-} == 24.04 ]] || {
      echo "Supported Ubuntu versions are 22.04 and 24.04; found '${VERSION_ID:-unknown}'." >&2
      exit 1
    }
    ;;
  debian)
    [[ ${VERSION_ID:-} == 12 ]] || {
      echo "Supported Debian version is 12; found '${VERSION_ID:-unknown}'." >&2
      exit 1
    }
    ;;
  *) echo "Supported distributions are Ubuntu and Debian; found '${ID:-unknown}'." >&2; exit 1 ;;
esac

if [[ -e /sys/fs/cgroup/cgroup.controllers ]]; then
  :
else
  echo "cgroup v2 is required (/sys/fs/cgroup/cgroup.controllers is missing)." >&2
  exit 1
fi

memory_kib=$(awk '/MemTotal:/ {print $2}' /proc/meminfo)
(( memory_kib >= 10 * 1024 * 1024 )) || { echo "At least 10 GiB RAM is required." >&2; exit 1; }
free_kib=$(df -Pk / | awk 'NR==2 {print $4}')
(( free_kib >= 20 * 1024 * 1024 )) || { echo "At least 20 GiB free disk is required." >&2; exit 1; }

if command -v docker >/dev/null 2>&1 && systemctl is-active --quiet docker.service; then
  if [[ -n $(docker ps -aq 2>/dev/null || true) ]]; then
    echo "A rootful Docker daemon has containers. Refusing to disable it automatically." >&2
    exit 1
  fi
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y ca-certificates curl dbus-user-session fuse-overlayfs git gnupg jq nftables openssl slirp4netns tar uidmap xz-utils

if ! command -v dockerd-rootless-setuptool.sh >/dev/null 2>&1; then
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL "https://download.docker.com/linux/${ID}/gpg" | gpg --dearmor --yes -o /etc/apt/keyrings/docker.gpg
  chmod a+r /etc/apt/keyrings/docker.gpg
  codename=${VERSION_CODENAME:-${UBUNTU_CODENAME:-}}
  [[ -n $codename ]] || { echo "Could not determine distribution codename." >&2; exit 1; }
  printf 'deb [arch=%s signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/%s %s stable\n' \
    "$arch" "$ID" "$codename" > /etc/apt/sources.list.d/docker.list
  apt-get update
  apt-get install -y docker-ce-cli docker-ce-rootless-extras docker-buildx-plugin docker-compose-plugin
fi

if ! id "$target_user" >/dev/null 2>&1; then
  useradd --create-home --shell /bin/bash "$target_user"
fi

if ! grep -q "^${target_user}:" /etc/subuid; then
  usermod --add-subuids 100000-165535 "$target_user"
fi
if ! grep -q "^${target_user}:" /etc/subgid; then
  usermod --add-subgids 100000-165535 "$target_user"
fi

target_uid=$(id -u "$target_user")
loginctl enable-linger "$target_user"
systemctl start "user@${target_uid}.service"

# This is a dedicated rootless deployment. Stop an empty rootful daemon created
# as a package-install side effect; never do this when it owns containers.
if systemctl is-active --quiet docker.service && [[ -z $(docker ps -aq 2>/dev/null || true) ]]; then
  systemctl disable --now docker.service docker.socket || true
fi

runtime_dir="/run/user/${target_uid}"
install -d -m 0700 -o "$target_user" -g "$target_user" "$runtime_dir"
runuser -u "$target_user" -- env \
  HOME="$(getent passwd "$target_user" | cut -d: -f6)" \
  XDG_RUNTIME_DIR="$runtime_dir" \
  DBUS_SESSION_BUS_ADDRESS="unix:path=${runtime_dir}/bus" \
  dockerd-rootless-setuptool.sh install --force

install -d -m 0750 -o "$target_user" -g "$target_user" \
  /srv/hermes /srv/hermes/projects /srv/hermes/wiki /srv/hermes/artifacts

cat <<EOF
Host preparation complete.

Next:
  1. Log in as ${target_user}.
  2. Put this repository at ~/hermes-deployment.
  3. Run bash ./scripts/bootstrap-user.sh.

Rootless socket: unix:///run/user/${target_uid}/docker.sock
EOF
