import os
import subprocess
import sys
from pathlib import Path

from constants import EJSON_KEYDIR


def main():
    if len(sys.argv) != 2:
        print("Usage: decrypt-ejson <environment_name>")
        return 1

    # Get environment name and strip any extension
    env_name = os.path.splitext(sys.argv[1])[0]

    # Construct the paths
    secrets_dir = Path(__file__).parent.parent.parent / "secrets"
    ejson_file_path = str(secrets_dir / f"{env_name}.ejson")
    json_file_path = str(secrets_dir / f"{env_name}.json")

    # Validate input file exists
    if not os.path.exists(ejson_file_path):
        print(f"Error: Input file {ejson_file_path} does not exist")
        return 1

    # Always use EJSON_KEYDIR
    ejson_keydir = os.getenv("EJSON_KEYDIR") or str(EJSON_KEYDIR)
    os.makedirs(ejson_keydir, exist_ok=True)
    env = os.environ.copy()
    env["EJSON_KEYDIR"] = ejson_keydir

    try:
        # Check if output file already exists
        if os.path.exists(json_file_path):
            print(f"Warning: Output file {json_file_path} already exists. It will be overwritten.")

        # Decrypt the file while preserving the original .ejson file
        subprocess.run(
            ["ejson", "decrypt", ejson_file_path, "-o", json_file_path],
            check=True,
            env=env,
            capture_output=True,
            text=True,
        )
        print(f"Successfully decrypted {ejson_file_path} to {json_file_path}")
        return 0

    except subprocess.CalledProcessError as e:
        print(f"Failed to decrypt ejson file:\nCommand: {e.cmd}\nError: {e.stderr}")
        # Clean up partial output file if it exists
        if os.path.exists(json_file_path):
            os.remove(json_file_path)
        return 1

    except FileNotFoundError:
        print("Error: ejson command not found. Please ensure ejson is installed and in your PATH.")
        return 1

    except Exception as e:
        print(f"An error occurred: {e}")
        # Clean up partial output file if it exists
        if os.path.exists(json_file_path):
            os.remove(json_file_path)
        return 1


if __name__ == "__main__":
    sys.exit(main())
