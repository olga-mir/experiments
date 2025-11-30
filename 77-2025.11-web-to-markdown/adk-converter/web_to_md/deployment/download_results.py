"""
Script to download scraped results from GCS.
"""
import argparse
import os
from google.cloud import storage

BUCKET_NAME = "web-to-md-bucket-7d4c11"

def download_folder(folder_name: str, destination_dir: str = "downloads"):
    """
    Downloads a folder from GCS to a local directory.

    Args:
        folder_name: The folder name in GCS (e.g., "2025-11-21_17_40_49").
        destination_dir: Local directory to save the files.
    """
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"Error initializing GCS client: {e}")
        return

    prefix = folder_name
    if not prefix.endswith("/"):
        prefix += "/"

    blobs = bucket.list_blobs(prefix=prefix)

    found = False
    for blob in blobs:
        found = True
        relative_path = blob.name
        local_path = os.path.join(destination_dir, relative_path)

        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        print(f"Downloading {blob.name} to {local_path}...")
        blob.download_to_filename(local_path)

    if not found:
        print(f"No files found in bucket '{BUCKET_NAME}' with prefix '{folder_name}'.")
    else:
        print(f"Download complete. Files saved to '{destination_dir}'")

def list_folders():
    """Lists the top-level folders (sessions) in the bucket."""
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"Error initializing GCS client: {e}")
        return

    # Use delimiter to list "directories"
    blobs = bucket.list_blobs(delimiter="/")
    # Trigger the iterator to populate prefixes
    list(blobs)

    print(f"Available sessions in '{BUCKET_NAME}':")
    if blobs.prefixes:
        for prefix in sorted(blobs.prefixes, reverse=True):
            print(f"  - {prefix.rstrip('/')}")
    else:
        print("  (No folders found)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download results from GCS")
    subparsers = parser.add_subparsers(dest="command")

    # List command
    list_parser = subparsers.add_parser("list", help="List available sessions")

    # Download command
    download_parser = subparsers.add_parser("get", help="Download a session folder")
    download_parser.add_argument("folder", help="Folder name (timestamp) to download")

    args = parser.parse_args()

    if args.command == "list":
        list_folders()
    elif args.command == "get":
        download_folder(args.folder)
    else:
        parser.print_help()
