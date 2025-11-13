#!/usr/bin/env bash
set -euo pipefail

# Usage: ./build_matrix.sh <event_name> <before_sha> <head_sha>

EVENT_NAME=$1
BEFORE_SHA=$2
HEAD_SHA=$3

declare -a MATRIX_ITEMS=()

# Helper function to add folder to matrix
add_to_matrix() {
  TYPE=$1
  SERVICE_DIR=$2
  NAME=$(basename "$SERVICE_DIR")
  MATRIX_ITEMS+=("{\"type\":\"$TYPE\",\"name\":\"$NAME\",\"folder\":\"$SERVICE_DIR\"}")
}

if [ "$EVENT_NAME" == "workflow_dispatch" ]; then
  echo "⚙️ Manual trigger: including all images"
  for TYPE in services jobs; do
    if [ -d "images/$TYPE" ]; then
      for SERVICE_DIR in images/$TYPE/*; do
        [ -d "$SERVICE_DIR" ] || continue
        add_to_matrix "$TYPE" "$SERVICE_DIR"
      done
    fi
  done
else
  # Determine diff range safely
  if [ -n "$BEFORE_SHA" ] && [ "$BEFORE_SHA" != "0000000000000000000000000000000000000000" ]; then
    DIFF_RANGE="$BEFORE_SHA $HEAD_SHA"
  else
    DIFF_RANGE="$HEAD_SHA~1 $HEAD_SHA"
  fi

  echo "🔍 Using diff range: $DIFF_RANGE"

  CHANGED=$(git diff --name-only $DIFF_RANGE | grep '^images/' || true)

  for path in $CHANGED; do
    TOP_FOLDER=$(echo "$path" | cut -d/ -f2)   # services or jobs
    SERVICE_NAME=$(echo "$path" | cut -d/ -f3)
    FOLDER_PATH="images/$TOP_FOLDER/$SERVICE_NAME"
    if [ -n "$SERVICE_NAME" ] && [ -d "$FOLDER_PATH" ]; then
      add_to_matrix "$TOP_FOLDER" "$FOLDER_PATH"
    fi
  done
fi

# Build JSON
MATRIX_JSON="["
if [ ${#MATRIX_ITEMS[@]} -gt 0 ]; then
  MATRIX_JSON+=$(IFS=,; echo "${MATRIX_ITEMS[*]}")
fi
MATRIX_JSON+="]"

# Output for GitHub Actions
echo "matrix=$MATRIX_JSON"
echo "::set-output name=matrix::$MATRIX_JSON"
