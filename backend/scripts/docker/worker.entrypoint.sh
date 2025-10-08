#!/bin/bash

source "$(dirname "$0")/common.entrypoint.sh"

# Load secrets and environment
load_secrets "$1"
setup_environment

beat_flag=""
if [ "$RUN_CELERY_BEAT" == "true" ]; then
    beat_flag="--beat"
fi

if [ "$ENVIRONMENT" == "development" ]; then
    poetry run poe serve worker $beat_flag --reload
else
    poetry run poe serve worker $beat_flag
fi
