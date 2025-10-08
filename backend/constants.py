"""Application constants."""

import os
from enum import Enum
from pathlib import Path

# EJSON key directory
EJSON_KEYDIR = Path(os.getenv("EJSON_KEYDIR") or Path("./ejson-keys"))

# Temporary environment file path for development
TMP_ENV_PATH = Path("./.env.tmp")


class Environment(str, Enum):
    """Environment types."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
