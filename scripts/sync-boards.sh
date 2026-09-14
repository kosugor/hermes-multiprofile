#!/usr/bin/env bash
set -Eeuo pipefail

projects_root=${HERMES_PROJECTS_ROOT:-/srv/hermes/projects}
wiki_root=${HERMES_WIKI_ROOT:-/srv/hermes/wiki}

[[ -d $projects_root && -r $projects_root ]] || { echo "Missing projects root: $projects_root" >&2; exit 1; }
[[ -d $wiki_root && -r $wiki_root ]] || { echo "Missing wiki root: $wiki_root" >&2; exit 1; }

hermes kanban init >/dev/null

board_json=$(hermes kanban boards list --json)
board_exists() {
  local slug=$1
  jq -e --arg slug "$slug" '
    (if type == "array" then . else (.boards // []) end)
    | any((.slug // .id) == $slug)
  ' <<<"$board_json" >/dev/null
}

create_board() {
  local slug=$1 name=$2 description=$3 workdir=$4
  if ! board_exists "$slug"; then
    hermes kanban boards create "$slug" --name "$name" --description "$description"
    board_json=$(hermes kanban boards list --json)
  fi
  hermes kanban boards set-default-workdir "$slug" "$workdir"
}

create_board wiki "Wiki Vault" "Reviewed durable knowledge and monitor snapshots" "$wiki_root"

while IFS= read -r -d '' repo; do
  [[ -e "$repo/.git" ]] || continue
  name=$(basename -- "$repo")
  slug=$(printf '%s' "$name" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9_-]+/-/g; s/^-+|-+$//g' | cut -c1-64)
  [[ -n $slug ]] || { echo "Cannot derive a board slug for $repo" >&2; exit 1; }
  [[ $slug != wiki && $slug != default ]] || { echo "Reserved board slug collision: $slug ($repo)" >&2; exit 1; }
  create_board "$slug" "$name" "Project repository: $repo" "$repo"
done < <(find "$projects_root" -mindepth 1 -maxdepth 1 -type d -print0)

echo "Kanban boards synchronized. The unavoidable default board remains an unbound control/inbox queue."
