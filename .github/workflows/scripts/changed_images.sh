#!/bin/bash
set -euo pipefail

EVENT_NAME=$1
CHANGED_FILES=$2

echo "EVENT_NAME='$EVENT_NAME'"
echo "CHANGED_FILES='$CHANGED_FILES'"

CHANGED_IMAGES=()

add_to_matrix() {
  TYPE=$1
  NAME=$2
  ENTRY="$TYPE/$NAME"
  for e in "${CHANGED_IMAGES[@]}"; do
    [[ "$e" == "$ENTRY" ]] && return
  done
  CHANGED_IMAGES+=("$ENTRY")
}

if [[ "$EVENT_NAME" == "workflow_dispatch" ]]; then
  for TYPE in services jobs; do
    for DIR in images/$TYPE/*/; do
      [ -d "$DIR" ] || continue
      NAME=$(basename "$DIR")
      add_to_matrix "$TYPE" "$NAME"
    done
  done
else
  while IFS= read -r file; do
    [[ "$file" != images/* ]] && continue
    TYPE=$(echo "$file" | cut -d/ -f2)
    NAME=$(echo "$file" | cut -d/ -f3)
    [ -d "images/$TYPE/$NAME" ] || continue
    add_to_matrix "$TYPE" "$NAME"
  done <<< "$CHANGED_FILES"
fi

# Build JSON using jq for safety
if [ ${#CHANGED_IMAGES[@]} -eq 0 ]; then
  MATRIX_JSON='[]'
else
  MATRIX_JSON=$(printf '%s\n' "${CHANGED_IMAGES[@]}" \
    | jq --raw-input . \
    | jq --compact-output --slurp \
        'map({type: (split("/")[0]), name: (split("/")[1]), folder: ("images/" + split("/")[0] + "/" + split("/")[1])})')
fi

# Debug
echo "Changed images matrix:"
echo "$MATRIX_JSON" | jq .

# Output matrix to GitHub Actions
echo "matrix=$MATRIX_JSON" >> $GITHUB_OUTPUT
