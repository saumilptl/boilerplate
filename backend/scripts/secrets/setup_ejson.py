import os
import sys
from pathlib import Path

from constants import EJSON_KEYDIR


def write_key(public_key: str, private_key: str, write_dir: Path) -> None:
    """Write the private key to the ejson-keys directory."""
    dest = write_dir / public_key
    write_dir.mkdir(parents=True, exist_ok=True)
    with open(dest, "w", encoding="utf-8") as f:
        f.write(private_key)


def main():
    """
    Setup EJSON keys using environment variables:
    - EJSON_PUBLIC_KEY: Required public key
    - EJSON_PRIVATE_KEY: Required private key
    - EJSON_KEYDIR: Optional key directory (default: ./ejson-keys)
    """
    # Get keys from environment
    public_key = os.getenv("EJSON_PUBLIC_KEY")
    private_key = os.getenv("EJSON_PRIVATE_KEY")

    # Require both keys
    if not public_key or not private_key:
        print("Error: Both EJSON_PUBLIC_KEY and EJSON_PRIVATE_KEY are required")
        sys.exit(1)

    # Get key directory - default to local directory instead of system directory
    write_dir = EJSON_KEYDIR

    try:
        write_key(public_key, private_key, write_dir)
        print(f"Successfully wrote key to {write_dir / public_key}")
    except PermissionError:
        print(f"Error: Cannot write to {write_dir}. Check directory permissions.")
        sys.exit(1)


if __name__ == "__main__":
    main()
