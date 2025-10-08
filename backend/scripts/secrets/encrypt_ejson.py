import os
import subprocess
import sys
from pathlib import Path

from constants import EJSON_KEYDIR


def main():
    if len(sys.argv) != 2:
        print("Usage: encrypt-ejson <environment_name>")
        return 1

    # Get environment name and strip any extension
    env_name = os.path.splitext(sys.argv[1])[0]

    # Construct the paths
    secrets_dir = Path(__file__).parent.parent.parent / "secrets"
    json_file_path = str(secrets_dir / f"{env_name}.json")
    ejson_file_path = str(secrets_dir / f"{env_name}.ejson")

    # Validate input JSON file exists
    if not os.path.exists(json_file_path):
        print(f"Error: Input file {json_file_path} does not exist")
        return 1

    # Always use EJSON_KEYDIR
    ejson_keydir = os.getenv("EJSON_KEYDIR") or str(EJSON_KEYDIR)
    os.makedirs(ejson_keydir, exist_ok=True)
    env = os.environ.copy()
    env["EJSON_KEYDIR"] = ejson_keydir

    try:
        # Run ejson encrypt - it will create an encrypted version of the file
        subprocess.run(
            ["ejson", "encrypt", json_file_path],
            check=True,
            env=env,
        )
        # Rename the encrypted file to .ejson
        os.rename(json_file_path, ejson_file_path)
        print(f"Successfully encrypted {json_file_path} to {ejson_file_path}")
        return 0

    except subprocess.CalledProcessError as e:
        print(f"Failed to encrypt json file:\nCommand: {e.cmd}\nError: {e.stderr}")
        return 1

    except FileNotFoundError:
        print("Error: ejson command not found. Please ensure ejson is installed and in your PATH.")
        return 1

    except Exception as e:
        print(f"An error occurred: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
