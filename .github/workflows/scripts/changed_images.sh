#!/bin/bash
set -euo pipefail

# Usage: ./changed_images.sh <event_name> <changed_files>
EVENT_NAME=$1
CHANGED_FILES=$2

# Array for changed images
CHANGED_IMAGES=()

# Flag to check if we need to rebuild all images
REBUILD_ALL=false

# Check if the event is workflow_dispatch to rebuild all
if [ "$EVENT_NAME" == "workflow_dispatch" ]; then
  REBUILD_ALL=true
fi

# Function to add folders to CHANGED_IMAGES avoiding duplicates
add_to_matrix() {
  TYPE=$1
  FOLDER=$2
  NAME=$(basename "$FOLDER")
  if ! printf '%s\n' "${CHANGED_IMAGES[@]}" | grep -qx "$TYPE/$NAME"; then
    CHANGED_IMAGES+=("$TYPE/$NAME")
  fi
}

if [ "$REBUILD_ALL" = true ]; then
  # Add all folders under services and jobs
  for TYPE in services jobs; do
    [ -d "images/$TYPE" ] || continue
    for FOLDER in images/$TYPE/*; do
      [ -d "$FOLDER" ] || continue
      add_to_matrix "$TYPE" "$FOLDER"
    done
  done
else
  # Only include folders for changed files
  for file in $CHANGED_FILES; do
    if [[ $file == images/* ]]; then
      TYPE=$(echo "$file" | cut -d/ -f2)
      NAME=$(echo "$file" | cut -d/ -f3)
      FOLDER="images/$TYPE/$NAME"
      [ -d "$FOLDER" ] || continue
      add_to_matrix "$TYPE" "$FOLDER"
    fi
  done
fi

# Create JSON matrix
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

# Debug info to stderr
echo "Matrix JSON: $MATRIX_JSON" >&2

# Output for GitHub Actions
echo "matrix=$MATRIX_JSON" >> $GITHUB_OUTPUT
