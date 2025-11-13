#!/bin/bash
set -euo pipefail

EVENT_NAME=$1
CHANGED_FILES=$2

CHANGED_IMAGES=()

add_to_matrix() {
  TYPE=$1
  NAME=$2
  ENTRY="$TYPE/$NAME"
  # Avoid duplicates
  for e in "${CHANGED_IMAGES[@]}"; do
    [[ "$e" == "$ENTRY" ]] && return
  done
  CHANGED_IMAGES+=("$ENTRY")
}

# If workflow_dispatch, rebuild all images under services and jobs
if [[ "$EVENT_NAME" == "workflow_dispatch" ]]; then
  for TYPE in services jobs; do
    for DIR in images/$TYPE/*/; do
      [ -d "$DIR" ] || continue
      NAME=$(basename "$DIR")
      add_to_matrix "$TYPE" "$NAME"
    done
  done
else
  # Process only changed files
  while IFS= read -r file; do
    [[ "$file" != images/* ]] && continue
    TYPE=$(echo "$file" | cut -d/ -f2)
    NAME=$(echo "$file" | cut -d/ -f3)
    [ -d "images/$TYPE/$NAME" ] || continue
    add_to_matrix "$TYPE" "$NAME"
  done <<< "$CHANGED_FILES"
fi

# Build JSON matrix
if [ ${#CHANGED_IMAGES[@]} -eq 0 ]; then
  MATRIX_JSON="[]"
else
  ITEMS=()
  for img in "${CHANGED_IMAGES[@]}"; do
    TYPE=$(echo "$img" | cut -d/ -f1)
    NAME=$(echo "$img" | cut -d/ -f2)
    FOLDER="images/$TYPE/$NAME"
    ITEMS+=("{\"type\":\"$TYPE\",\"name\":\"$NAME\",\"folder\":\"$FOLDER\"}")
  done
  MATRIX_JSON="["
  MATRIX_JSON+=$(IFS=,; echo "${ITEMS[*]}")
  MATRIX_JSON+="]"
fi

# Debug
echo "Matrix JSON: $MATRIX_JSON" >&2

# Output for GitHub Actions
echo "matrix=$MATRIX_JSON" >> $GITHUB_OUTPUT
