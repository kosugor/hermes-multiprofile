#!/usr/bin/env bash
set -Eeuo pipefail

usage() {
  echo "Usage: $0 ARCHIVE NEW_EMPTY_STAGING_DIRECTORY" >&2
}

[[ $# -eq 2 ]] || { usage; exit 2; }
archive=$1
target=$2

[[ -f $archive ]] || { echo "Archive not found: $archive" >&2; exit 1; }
archive=$(realpath -e -- "$archive")
target=$(realpath -m -- "$target")

case "$target" in
  /|"$HOME"|/srv|/srv/hermes|"${HERMES_HOME:-$HOME/.hermes}")
    echo "Refusing unsafe restore target: $target" >&2
    exit 1
    ;;
esac

if [[ -e $target ]]; then
  [[ -d $target ]] || { echo "Restore target exists and is not a directory." >&2; exit 1; }
  [[ -z $(find "$target" -mindepth 1 -maxdepth 1 -print -quit) ]] || {
    echo "Restore target must be empty: $target" >&2
    exit 1
  }
else
  install -d -m 0700 "$target"
fi

if [[ -f $archive.sha256 ]]; then
  (cd -- "$(dirname -- "$archive")" && sha256sum -c -- "$(basename -- "$archive.sha256")")
else
  echo "Warning: no adjacent checksum file was found." >&2
fi

while IFS= read -r entry; do
  case "$entry" in
    /*|../*|*/../*|*/..)
      echo "Unsafe archive member: $entry" >&2
      exit 1
      ;;
  esac
done < <(tar -tzf "$archive")

tar --no-same-owner --no-same-permissions -xzf "$archive" -C "$target"
chmod 0700 "$target"

cat <<EOF
Restore staged at: $target

Nothing was installed in place. Review MANIFEST.txt and the staged files, stop
Hermes, then deliberately copy the approved paths into their final locations.
Run bootstrap first to recreate the managed Hermes, Node, QMD, and browser
runtimes; then restore the approved state paths. Keep the original backup until
validation and service startup both succeed.
EOF
