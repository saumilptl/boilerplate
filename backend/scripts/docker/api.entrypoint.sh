#!/bin/bash

source "$(dirname "$0")/common.entrypoint.sh"

# Load secrets and environment
load_secrets "$1"
setup_environment


# Run migrations
poetry run poe migration-upgrade

if [ "$ENVIRONMENT" == "development" ]; then
    poetry run poe serve api --reload
else
    poetry run poe serve api
fi
