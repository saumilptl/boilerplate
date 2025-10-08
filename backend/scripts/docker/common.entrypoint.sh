#!/bin/bash
source "$(dirname "$0")/../../env_constants.sh"

if [ "$ENVIRONMENT" == "development" ]; then
    echo "Development environment detected. Installing package from mounted source..."
    cd /app/src && poetry install
    cd - > /dev/null  # Return to previous directory
fi

load_secrets() {
    local force_flag=""

    # Check for force flag
    if [ "$1" == "-f" ]; then
        force_flag="--force"
    fi

    poetry run setup-ejson \
      && poetry run load-env $force_flag

    # Check if the secrets loading was successful
    if [ $? -ne 0 ]; then
        echo "Failed to load secrets. Exiting."
        exit 1
    fi
}

setup_environment() {
    if [ -f "$TMP_ENV_PATH" ]; then
        set -a
        source "$TMP_ENV_PATH"
        set +a

        shred -u "$TMP_ENV_PATH"
    fi
}
