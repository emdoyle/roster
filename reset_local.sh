#!/bin/bash

# Initialize variables
TESTDATA="/Users/evanmdoyle/Programming/roster/examples"
ROSTERURL="http://localhost:7888/v0.1"
CONTENTTYPE="Content-Type: application/json"

# Function to convert filename to PascalCase
to_pascal_case() {
  echo "$1" | awk 'BEGIN{FS=OFS="_"}{for(i=1;i<=NF;i++)$i=toupper(substr($i,1,1)) tolower(substr($i,2));}1'
}

# Function to create or update a resource using POST then PATCH if necessary
create_or_update_resource() {
  local filepath="$1"
  local relativepath="${filepath#${TESTDATA}/}"
  local filename=$(basename "$filepath" .json)
  local parentdir=$(dirname "$relativepath")

  # Convert filename to PascalCase for PATCH endpoint
  local pascal_case_filename=$(to_pascal_case "$filename")
  local post_endpoint="/${parentdir}"
  local patch_endpoint="/${parentdir}/${pascal_case_filename}"

  echo "Attempting to create resource from $filepath using POST request to $post_endpoint ..."

  # Attempt POST request
  local post_status=$(curl -s -o /dev/null -w "%{http_code}" -X POST -H "$CONTENTTYPE" "${ROSTERURL}${post_endpoint}" -d "@${filepath}")

  # Check if POST was successful
  if [[ $post_status -eq 201 || $post_status -eq 200 ]]; then
    echo "Successfully created resource from $filepath."
  else
    echo "POST request failed with status code $post_status. Attempting to update resource using PATCH request to $patch_endpoint ..."

    # Attempt PATCH request
    local patch_status=$(curl -s -o /dev/null -w "%{http_code}" -X PATCH -H "$CONTENTTYPE" "${ROSTERURL}${patch_endpoint}" -d "@${filepath}")

    if [[ $patch_status -eq 200 ]]; then
      echo "Successfully updated resource from $filepath."
    else
      echo "Failed to update resource from $filepath. PATCH request returned status code $patch_status."
    fi
  fi
}

# Loop through each JSON file in the examples subdirectories and attempt to create or update the corresponding resource
find "$TESTDATA" -mindepth 2 -type f -name "*.json" | while read -r filepath; do
  create_or_update_resource "$filepath"
done
