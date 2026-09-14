#!/usr/bin/env bash
set -Eeuo pipefail

usage() {
  echo "Usage: sudo $0 [--user USER] [--apply]" >&2
}

target_user=hermes
apply=0
while (($#)); do
  case "$1" in
    --user)
      [[ $# -ge 2 ]] || { usage; exit 2; }
      target_user=$2
      shift 2
      ;;
    --apply)
      apply=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *) usage; exit 2 ;;
  esac
done

[[ $EUID -eq 0 ]] || { echo "Run as root." >&2; exit 1; }
target_uid=$(id -u "$target_user")

rules=$(cat <<EOF
table inet hermes_egress {
  chain output {
    type filter hook output priority filter; policy accept;
    ct state established,related accept
    meta skuid ${target_uid} ip daddr 127.0.0.0/8 accept
    meta skuid ${target_uid} ip6 daddr ::1/128 accept
    meta skuid ${target_uid} ip daddr { 0.0.0.0/8, 10.0.0.0/8, 100.64.0.0/10, 127.0.0.0/8, 169.254.0.0/16, 172.16.0.0/12, 192.0.0.0/24, 192.0.2.0/24, 192.168.0.0/16, 198.18.0.0/15, 198.51.100.0/24, 203.0.113.0/24, 224.0.0.0/4, 240.0.0.0/4 } reject
    meta skuid ${target_uid} ip6 daddr { ::/128, ::ffff:0.0.0.0/104, ::ffff:10.0.0.0/104, ::ffff:100.64.0.0/106, ::ffff:127.0.0.0/104, ::ffff:169.254.0.0/112, ::ffff:172.16.0.0/108, ::ffff:192.0.0.0/120, ::ffff:192.0.2.0/120, ::ffff:192.168.0.0/112, ::ffff:198.18.0.0/111, ::ffff:198.51.100.0/120, ::ffff:203.0.113.0/120, ::ffff:224.0.0.0/100, ::ffff:240.0.0.0/100, fc00::/7, fe80::/10, ff00::/8 } reject
  }
}
EOF
)

if (( apply == 0 )); then
  printf '%s\n' "$rules"
  echo "Preview only. Re-run with --apply to install." >&2
  exit 0
fi

command -v nft >/dev/null 2>&1 || { echo "nft is required." >&2; exit 1; }
tmp=$(mktemp)
trap 'rm -f -- "$tmp"' EXIT
printf '%s\n' "$rules" > "$tmp"
# Syntax-check with a throwaway table name so a previously installed policy
# cannot make an idempotent re-run fail with "File exists".
check_rules=${rules//hermes_egress/hermes_egress_check}
printf '%s\n' "$check_rules" > "$tmp"
nft --check -f "$tmp"
printf '%s\n' "$rules" > "$tmp"

install -d -m 0755 /etc/nftables.d
if [[ -f /etc/nftables.d/hermes-egress.nft ]]; then
  cp -p /etc/nftables.d/hermes-egress.nft "/etc/nftables.d/hermes-egress.nft.bak.$(date -u +%Y%m%dT%H%M%SZ)"
fi
install -m 0644 "$tmp" /etc/nftables.d/hermes-egress.nft

if ! grep -Eq '^include[[:space:]]+"/etc/nftables\.d/\*\.nft"' /etc/nftables.conf; then
  printf '\ninclude "/etc/nftables.d/*.nft"\n' >> /etc/nftables.conf
fi

if nft list table inet hermes_egress >/dev/null 2>&1; then
  nft delete table inet hermes_egress
fi
nft -f /etc/nftables.d/hermes-egress.nft
systemctl enable --now nftables.service
echo "Installed Hermes UID egress guard for $target_user ($target_uid)."
