#!/usr/bin/env bash
set -euo pipefail

EVENT_NAME=$1
BEFORE_SHA=$2
HEAD_SHA=$3

MATRIX_ITEMS=()

add_to_matrix() {
  TYPE=$1
  FOLDER=$2
  NAME=$(basename "$FOLDER")
  # Only include if Dockerfile exists
  if [ -f "$FOLDER/Dockerfile" ]; then
    MATRIX_ITEMS+=("{\"type\":\"$TYPE\",\"name\":\"$NAME\",\"folder\":\"$FOLDER\"}")
  fi
}

# Include all on manual run
if [ "$EVENT_NAME" == "workflow_dispatch" ]; then
  for TYPE in services jobs; do
    [ -d "images/$TYPE" ] || continue
    for FOLDER in images/$TYPE/*; do
      [ -d "$FOLDER" ] || continue
      add_to_matrix "$TYPE" "$FOLDER"
    done
  done
else
  # Detect changes on push
  if [ -n "$BEFORE_SHA" ] && [ "$BEFORE_SHA" != "0000000000000000000000000000000000000000" ]; then
    DIFF_RANGE="$BEFORE_SHA $HEAD_SHA"
  else
    DIFF_RANGE="$HEAD_SHA~1 $HEAD_SHA"
  fi

  CHANGED=$(git diff --name-only $DIFF_RANGE | grep '^images/' || true)
  for path in $CHANGED; do
    TYPE=$(echo "$path" | cut -d/ -f2)
    NAME=$(echo "$path" | cut -d/ -f3)
    FOLDER="images/$TYPE/$NAME"
    [ -d "$FOLDER" ] || continue
    add_to_matrix "$TYPE" "$FOLDER"
  done
fi

# Build JSON array
if [ ${#MATRIX_ITEMS[@]} -gt 0 ]; then
  MATRIX_JSON="["
  MATRIX_JSON+=$(IFS=,; echo "${MATRIX_ITEMS[*]}")
  MATRIX_JSON+="]"
else
  MATRIX_JSON="[]"
fi

# Output for GitHub Actions
echo "::set-output name=matrix::$MATRIX_JSON"
