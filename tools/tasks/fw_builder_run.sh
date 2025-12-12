#!/bin/bash

set -euo pipefail

CONTAINER="toor-dev-demo-project-firmware-builder"
FW_ROOT="/workspace/toor-dev-demo-project-fw"

# Ensure the container is running
if ! docker ps --format "{{.Names}}" | grep -q "^${CONTAINER}$"; then
    echo "Error: Container '${CONTAINER}' is not running."
    exit 1
fi

# Ensure user passed something
if [[ $# -eq 0 ]]; then
    echo "Usage: ./fw_builder_run.sh <command> [args...]"
    echo "Example: ./fw_builder_run.sh scripts/project-build.sh"
    echo "Example: ./fw_builder_run.sh make clean"
    exit 1
fi

# If first argument is a file path (relative), prefix it with firmware root
CMD="$@"
FIRST="$1"

if [[ -f "${FIRST}" || "${FIRST}" == */* ]]; then
    # Call script relative to firmware folder
    ABS="${FW_ROOT}/${FIRST}"
    shift
    docker exec -it "${CONTAINER}" bash -lc "cd ${FW_ROOT} && ${ABS} $*"
else
    # Plain command (make, cmake, bash, etc.)
    docker exec -it "${CONTAINER}" bash -lc "cd ${FW_ROOT} && $CMD"
fi
