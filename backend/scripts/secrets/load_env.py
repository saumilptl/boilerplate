import logging
import os

import typer

from constants import Environment
from scripts.secrets.secret_loader import SecretsLoader

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

app = typer.Typer()


@app.command()
def main(
    force: bool = typer.Option(False, "--force", "-f", help="Force override existing environment variables"),
) -> None:
    """
    Load environment variables from EJSON secrets file.
    Only secrets prefixed with ENV_ will be loaded into environment.
    """
    try:
        if os.getenv("ENVIRONMENT"):
            environment_str = os.getenv("ENVIRONMENT").lower()
        else:
            logger.warning("ENVIRONMENT variable not set. Defaulting to 'development'.")
            environment_str = "development"

        current_environment = Environment(environment_str)

        logger.info("Loading environment variables for %s environment", current_environment)

        secrets_loader = SecretsLoader(current_environment, force)
        secrets_loader.load_ejson_secrets()
        secrets_loader.load_environment_variables()

        logger.info("Successfully loaded environment variables")

    except Exception:
        logger.exception("Failed to load environment variables")
        raise typer.Exit(code=1) from None


if __name__ == "__main__":
    app()
