#!/bin/bash
set -euo pipefail

EVENT_NAME=$1
CHANGED_FILES=$2

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

# Output JSON
MATRIX_JSON="["
for i in "${!CHANGED_IMAGES[@]}"; do
  TYPE=$(echo "${CHANGED_IMAGES[i]}" | cut -d/ -f1)
  NAME=$(echo "${CHANGED_IMAGES[i]}" | cut -d/ -f2)
  FOLDER="images/$TYPE/$NAME"
  MATRIX_JSON+="{\"type\":\"$TYPE\",\"name\":\"$NAME\",\"folder\":\"$FOLDER\"}"
  [[ $i -lt $((${#CHANGED_IMAGES[@]}-1)) ]] && MATRIX_JSON+=","
done
MATRIX_JSON+="]"

echo "matrix=$MATRIX_JSON" >> $GITHUB_OUTPUT
