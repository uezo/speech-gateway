#!/bin/bash

set -e

# Load only DATA_PATH from .env to avoid parsing unrelated entries
if [ -f .env ]; then
    DATA_PATH_LINE=$(grep -E '^[[:space:]]*DATA_PATH=' .env | tail -n 1 || true)
    if [ -n "$DATA_PATH_LINE" ]; then
        DATA_PATH_VALUE=${DATA_PATH_LINE#*=}
        DATA_PATH_VALUE=${DATA_PATH_VALUE%$'\r'}
        DATA_PATH_VALUE=$(printf '%s' "$DATA_PATH_VALUE" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' -e 's/^"\(.*\)"$/\1/' -e "s/^'\(.*\)'$/\1/")
    fi
fi

# Default to ../data if DATA_PATH is not set
DATA_PATH=${DATA_PATH:-../data}

echo "Setting up volumes at: $DATA_PATH"

# Create directories if they don't exist
mkdir -p "$DATA_PATH/postgres"
mkdir -p "$DATA_PATH/pgadmin"

# Set appropriate permissions
# PostgreSQL needs UID 999 (in most PostgreSQL Docker images)
# PgAdmin needs UID 5050
if [ "$(uname)" = "Linux" ]; then
    sudo chown -R 999:999 "$DATA_PATH/postgres" 2>/dev/null || true
    sudo chown -R 5050:5050 "$DATA_PATH/pgadmin" 2>/dev/null || true
fi

echo "Volume directories created successfully:"
