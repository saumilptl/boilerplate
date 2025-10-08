import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Any

from dotenv import set_key

from constants import EJSON_KEYDIR, TMP_ENV_PATH, Environment

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


class SecretKeyCollisionError(Exception):
    """Raised when two secret keys map to the same name after prefix stripping."""

    pass


class EnvVarCollisionError(Exception):
    """Raised when multiple secret paths map to the same environment variable."""

    pass


class SecretsLoader:
    """
    Manages loading and processing of secrets from EJSON files.

    This class implements a convention where secrets in EJSON files can be either:
    1. Environment variables (prefixed with ENV_)
    2. Internal secrets (no ENV_ prefix)

    EJSON file structure example:
    {
        "_public_key": "unencrypted-value",          # Unencrypted (EJSON convention)
        "ENV_API_KEY": "EJ[encrypted:value]",        # Encrypted environment variable
        "_ENV_DEBUG": "true",                        # Unencrypted environment variable
        "INTERNAL_SECRET": "EJ[encrypted:value]",    # Internal encrypted secret
        "nested": {                                  # Nested structure example
            "ENV_NESTED_KEY": "nested-value",        # Will be available as NESTED_KEY env var
            "auth": {
                "_ENV_DEBUG_MODE": "true"            # Will be available as DEBUG_MODE env var
            }
        }
    }

    Only secrets with the ENV_ prefix (after removing any leading underscore)
    will be loaded into environment variables, including from nested dictionaries.

    Additionally, when force=False, any secret value can be overridden by
    a corresponding environment variable that already exists.
    """

    def __init__(self, env: Environment, force: bool):
        """
        Initialize the SecretsLoader.

        Args:
            env: The target environment
            force: Whether to force override existing environment variables.
                  When False, environment variables override secrets instead.
        """
        self.environment = env
        self.force = force
        self._secrets: dict[str, Any] = {}

    def load_ejson_secrets(self) -> dict[str, Any]:
        """
        Load and decrypt secrets from EJSON files.

        Returns:
            Dict[str, Any]: Complete dictionary of decrypted secrets with prefixes stripped

        Raises:
            FileNotFoundError: If required EJSON file is missing
            RuntimeError: If decryption fails
            Exception: For any other unexpected errors during secret loading
        """
        self._secrets = self._load_and_decrypt_secrets()

        # Apply environment variable overrides if force is False
        if not self.force:
            logger.info("Checking for environment variables that override secrets...")
            self._apply_env_overrides()

        # Return a copy with prefixes stripped
        return self._strip_prefixes(self._secrets)

    def _strip_prefixes(self, secrets_dict: dict[str, Any]) -> dict[str, Any]:
        """
        Strip ENV_ and leading underscore prefixes from keys in the secrets dictionary.

        Args:
            secrets_dict: The original secrets dictionary

        Returns:
            Dict[str, Any]: A new dictionary with prefixes stripped from keys

        Raises:
            SecretKeyCollisionError: If two different keys map to the same stripped key
        """
        result = {}
        collision_map = {}  # Track {stripped_key: original_key}

        for key, value in secrets_dict.items():
            # Keep EJSON special keys as is
            if key == "_public_key":
                result[key] = value
                continue

            # Process key name - strip prefixes
            new_key = key
            if new_key.startswith("_"):
                new_key = new_key[1:]

            if new_key.startswith("ENV_"):
                new_key = new_key[4:]

            # Process nested dictionaries recursively
            if isinstance(value, dict):
                try:
                    result[new_key] = self._strip_prefixes(value)
                except SecretKeyCollisionError as e:
                    # Propagate nested error with path context
                    raise SecretKeyCollisionError(f"In '{key}': {e!s}") from e
            else:
                # Check for collisions
                if new_key in result:
                    raise SecretKeyCollisionError(
                        f"Key collision detected: '{key}' and '{collision_map[new_key]}' "
                        f"both map to the same key '{new_key}' after stripping prefixes"
                    )

                result[new_key] = value
                collision_map[new_key] = key  # Track which original key created this entry

        return result

    def _apply_env_overrides(self) -> None:
        """
        Override secret values with environment variables when force=False.

        This creates a bidirectional relationship:
        - When force=True: secrets override environment variables
        - When force=False: environment variables override secrets
        """

        def process_dict(secrets_dict: dict[str, Any], path: str = "") -> None:
            """
            Recursively process a dictionary to override values from env vars.

            Args:
                secrets_dict: The secrets dictionary to process
                path: Current path in the nested structure (for logging)
            """
            for key, value in list(secrets_dict.items()):
                # Skip EJSON special keys
                if key == "_public_key":
                    continue

                # Determine the environment variable name to check
                # Strip leading underscore if present
                processed_key = key[1:] if key.startswith("_") else key
                current_path = f"{path}.{key}" if path else key

                # For ENV_ prefixed secrets, check for the variable without the prefix
                env_var_name = processed_key[4:] if processed_key.startswith("ENV_") else processed_key

                # Check if environment variable exists
                if env_var_name in os.environ:
                    # Convert environment value to appropriate type and apply override
                    secrets_dict[key] = self._convert_env_value(os.environ[env_var_name], secrets_dict[key])

                    # Log override without revealing values
                    logger.debug(
                        "OVERRIDE: Environment variable %s overrides secret %s",
                        env_var_name,
                        current_path,
                    )

                # Recursively process nested dictionaries
                if isinstance(value, dict):
                    process_dict(value, current_path)

        # Start processing from the root
        process_dict(self._secrets)

    def _convert_env_value(self, env_value: str, original_value: Any) -> Any:
        """
        Convert environment variable string to appropriate type based on original value.

        Args:
            env_value: String value from environment variable
            original_value: Original value from secrets to determine type

        Returns:
            Converted value matching the type of original value when possible
        """
        # If original is bool, convert accordingly
        if isinstance(original_value, bool):
            return env_value.lower() == "true"

        # If original is int, try to convert
        if isinstance(original_value, int):
            try:
                return int(env_value)
            except ValueError:
                # Fall back to string if conversion fails
                return env_value

        # If original is float, try to convert
        if isinstance(original_value, float):
            try:
                return float(env_value)
            except ValueError:
                return env_value

        # If original is dict or list, try to parse JSON
        if isinstance(original_value, dict | list):
            try:
                return json.loads(env_value)
            except json.JSONDecodeError:
                # Return as string if not valid JSON
                return env_value

        # Default case: return as string
        return env_value

    def load_environment_variables(self) -> None:
        """
        Load ENV_ prefixed secrets into environment variables.
        Must be called after load_ejson_secrets().

        Raises:
            RuntimeError: If called before loading secrets
        """
        if not self._secrets:
            raise RuntimeError("Secrets must be loaded before setting environment variables")
        self._load_env_variables()

    def _load_and_decrypt_secrets(self) -> dict[str, Any]:
        """
        Internal method to load and decrypt secrets from EJSON files.

        Returns:
            Dict[str, Any]: Decrypted secrets dictionary
        """
        ejson_file = Path(f"./secrets/{self.environment.lower()}.ejson")
        if not ejson_file.exists():
            logger.error("EJSON file not found: %s", ejson_file)
            raise FileNotFoundError(f"EJSON file not found: {ejson_file}")

        json_file = ejson_file.with_suffix(".json")

        try:
            if not json_file.exists():
                self._decrypt_ejson(self.environment.lower())

            # Load all secrets from the decrypted file
            with open(json_file, encoding="utf-8") as f:
                secrets = json.load(f)

            # Merge local secrets in development
            if self.environment == Environment.DEVELOPMENT:
                secrets = self._merge_local_secrets(secrets)

            logger.info("Loaded secrets for %s environment.", self.environment)

            # Cleanup decrypted file
            if json_file.exists() and self.environment != Environment.DEVELOPMENT:
                json_file.unlink()

            return secrets

        except Exception:
            logger.exception("Failed to process secrets")
            if json_file.exists():
                json_file.unlink()
            raise

    def _decrypt_ejson(self, environment: str) -> None:
        """
        Decrypt the EJSON file using ejson decrypt command.

        Args:
            environment: The environment name for EJSON file

        Raises:
            RuntimeError: If decryption fails
        """
        try:
            # Set EJSON_KEYDIR environment variable
            ejson_keydir = os.getenv("EJSON_KEYDIR") or str(EJSON_KEYDIR)
            os.makedirs(ejson_keydir, exist_ok=True)
            env = os.environ.copy()
            env["EJSON_KEYDIR"] = ejson_keydir

            ejson_file = Path(f"./secrets/{environment}.ejson")
            json_file = Path(f"./secrets/{environment}.json")

            subprocess.run(
                ["ejson", "decrypt", str(ejson_file), "-o", str(json_file)],
                check=True,
                capture_output=True,
                text=True,
                env=env,
            )
        except subprocess.CalledProcessError as e:
            logger.exception("Failed to decrypt EJSON file for: %s\nError: %s", environment, e.stderr)
            raise RuntimeError(f"Failed to decrypt EJSON file: {e}") from e

    def _merge_local_secrets(self, secrets: dict[str, Any]) -> dict[str, Any]:
        """
        Merge local.json secrets if present in development environment.
        Local secrets take precedence over environment secrets with deep merging.

        Args:
            secrets: The current secrets dictionary

        Returns:
            Dict[str, Any]: Updated secrets dictionary with local secrets merged
        """
        local_secrets_file = Path("./secrets/local.json").resolve()
        if local_secrets_file.exists():
            with open(local_secrets_file, encoding="utf-8") as f:
                local_secrets = json.load(f)

            # Deep merge implementation inline
            def deep_merge(original: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
                result = original.copy()
                for k, v in override.items():
                    if k in result and isinstance(result[k], dict) and isinstance(v, dict):
                        result[k] = deep_merge(result[k], v)
                    else:
                        result[k] = v
                return result

            secrets = deep_merge(secrets, local_secrets)
            logger.info("Merged local secrets from %s", local_secrets_file)
        return secrets

    def _load_env_variables(self) -> None:
        """
        Load ENV_ prefixed secrets into environment variables, including from nested dictionaries.

        Raises:
            EnvVarCollisionError: If multiple secret paths map to the same environment variable
        """
        # Track which env vars are set from which paths
        env_var_sources = {}

        def process_dict(secrets_dict: dict[str, Any], path: str = "") -> None:
            """
            Recursively process a dictionary for environment variables.

            Args:
                secrets_dict: Dictionary to process
                path: Current path in the nested structure (for logging)
            """
            for key, value in secrets_dict.items():
                # Process current key for ENV_ variables
                processed_key = key[1:] if key.startswith("_") else key
                current_path = f"{path}.{key}" if path else key

                if processed_key.startswith("ENV_"):
                    env_var_name = processed_key[4:]

                    # Check for collision
                    if env_var_name in env_var_sources:
                        raise EnvVarCollisionError(
                            f"Environment variable '{env_var_name}' is defined in multiple places: "
                            f"'{env_var_sources[env_var_name]}' and '{current_path}'"
                        )

                    env_var_sources[env_var_name] = current_path

                    # Check existing environment variable
                    existing_value = os.getenv(env_var_name)
                    if existing_value is not None and not self.force:
                        logger.info(
                            "Environment variable %s already exists. Skipping.",
                            env_var_name,
                        )
                        continue

                    # Process and set the value
                    processed_value = self._process_value(value)
                    os.environ[env_var_name] = processed_value
                    set_key(TMP_ENV_PATH, env_var_name, processed_value)

                    if existing_value is not None and self.force:
                        logger.info(
                            "OVERRIDE: Secret '%s' overrides environment variable '%s'",
                            current_path,
                            env_var_name,
                        )
                    else:
                        logger.info(
                            "SET: Environment variable '%s' set from secret '%s'",
                            env_var_name,
                            current_path,
                        )

                # Recursively process nested dictionaries
                if isinstance(value, dict):
                    process_dict(value, current_path)

        # Start processing from the root secrets dictionary
        process_dict(self._secrets)

    @staticmethod
    def _process_value(value: Any) -> str:
        """
        Convert various value types to string format for environment variables.

        Args:
            value: The value to process (bool, list, dict, or other)

        Returns:
            str: The processed string value
        """
        if isinstance(value, bool):
            return str(value).lower()
        if isinstance(value, list | dict):
            return json.dumps(value)
        return str(value)
