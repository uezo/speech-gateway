#!/bin/bash

# Setup script for Docker volumes
# This script creates necessary directories for Docker named volumes

set -e

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Default to ./data if DATA_PATH is not set
DATA_PATH=${DATA_PATH:-./data}

echo "Setting up volumes at: $DATA_PATH"

# Create directories if they don't exist
mkdir -p "$DATA_PATH/postgres"
mkdir -p "$DATA_PATH/pgadmin"
mkdir -p "$DATA_PATH/cache"

# Set appropriate permissions
# PostgreSQL needs UID 999 (in most PostgreSQL Docker images)
# PgAdmin needs UID 5050
if [ "$(uname)" = "Linux" ]; then
    sudo chown -R 999:999 "$DATA_PATH/postgres" 2>/dev/null || true
    sudo chown -R 5050:5050 "$DATA_PATH/pgadmin" 2>/dev/null || true
fi

echo "Volume directories created successfully:"
echo "  - $DATA_PATH/postgres"
echo "  - $DATA_PATH/pgadmin"
echo "  - $DATA_PATH/cache"
echo ""
echo "You can now run: docker compose up -d"
