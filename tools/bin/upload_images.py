#!/usr/bin/env python3
"""
Stand-alone tool to upload a directory of images via the upload_image API endpoint.
After uploading, associates images with books based on filename convention.

Filename Convention:
    Images should be named with the book ID as the first characters before an underscore.
    Example: "124_image_of_book_cover.png" -> book_id = 124

Usage:
    python upload_images.py <directory_path>
    python upload_images.py <directory_path> --recursive
    python upload_images.py <directory_path> --extensions jpg,png,gif
"""

import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import quote

import requests

CONFIG_PATH = "/book_service/config/configuration.json"  # root is "tools"


def get_config():
    """Load configuration from configuration.json file."""
    config_paths = [
        f".{CONFIG_PATH}",
        f"..{CONFIG_PATH}",
        "../book_service/config/configuration.json",
        "./book_service/config/configuration.json"
    ]

    for config_path in config_paths:
        try:
            with open(config_path, "r") as cfile:
                config = json.load(cfile)
                endpoint = config["endpoint"]
                api_key = config["api_key"]
                return endpoint, api_key
        except (OSError, FileNotFoundError, KeyError):
            continue

    print("ERROR: Configuration file not found!")
    print(f"Tried paths: {config_paths}")
    sys.exit(1)


def get_image_files(directory, recursive=False, extensions=None):
    """
    Get list of image files from the specified directory.

    Args:
        directory: Path to the directory containing images
        recursive: If True, search subdirectories recursively
        extensions: List of file extensions to include (e.g., ['jpg', 'png'])

    Returns:
        List of Path objects for image files
    """
    if extensions is None:
        extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'tiff']

    # Normalize extensions (remove dots, convert to lowercase)
    extensions = [ext.lower().lstrip('.') for ext in extensions]

    directory_path = Path(directory)

    if not directory_path.exists():
        print(f"ERROR: Directory '{directory}' does not exist!")
        sys.exit(1)

    if not directory_path.is_dir():
        print(f"ERROR: '{directory}' is not a directory!")
        sys.exit(1)

    image_files = []

    if recursive:
        pattern = "**/*"
    else:
        pattern = "*"

    for file_path in directory_path.glob(pattern):
        if file_path.is_file():
            ext = file_path.suffix.lower().lstrip('.')
            if ext in extensions:
                image_files.append(file_path)

    return sorted(image_files)


def upload_image(endpoint, api_key, file_path, custom_filename=None):
    """
    Upload a single image file to the API endpoint.

    Args:
        endpoint: API endpoint URL
        api_key: API key for authentication
        file_path: Path to the image file
        custom_filename: Optional custom filename for the uploaded file

    Returns:
        Tuple of (success: bool, response_data: dict)
    """
    url = f"{endpoint}/upload_image"
    headers = {'x-api-key': api_key}

    try:
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f, f'image/{file_path.suffix.lstrip(".")}')}
            data = {}
            if custom_filename:
                data['filename'] = custom_filename

            response = requests.post(url, files=files, data=data, headers=headers, timeout=30)

            if response.status_code == 200:
                return True, response.json()
            else:
                return False, response.json() if response.text else {"error": f"HTTP {response.status_code}"}

    except requests.exceptions.RequestException as e:
        return False, {"error": str(e)}
    except Exception as e:
        return False, {"error": f"Unexpected error: {str(e)}"}


def extract_book_id(filename):
    """
    Extract book ID from filename.

    Expects filenames in the format: "<book_id>_<description>.<ext>"
    Example: "124_image_of_book_cover.png" -> 124

    Args:
        filename: The image filename (string or Path object)

    Returns:
        int: The extracted book ID, or None if no valid ID found
    """
    filename_str = str(filename)

    # Extract the first part before underscore
    match = re.match(r'^(\d+)_', filename_str)

    if match:
        return int(match.group(1))

    return None


def is_safe_filename(filename):
    """
    Validate that a filename is safe for use in URLs and file systems.

    Security checks:
    - No directory traversal sequences (../, ..\, etc.)
    - No null bytes
    - No control characters
    - Reasonable length (max 255 characters)
    - Only safe characters: alphanumeric, underscore, hyphen, dot
    - Not empty or just dots
    - Valid image extension

    Args:
        filename: The filename to validate (string or Path object)

    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    filename_str = str(filename)

    # Check for empty or too long
    if not filename_str or len(filename_str) == 0:
        return False, "Filename is empty"

    if len(filename_str) > 255:
        return False, f"Filename too long ({len(filename_str)} chars, max 255)"

    # Check for directory traversal attempts
    if '..' in filename_str:
        return False, "Filename contains directory traversal sequence (..)"

    # Check for path separators
    if '/' in filename_str or '\\' in filename_str:
        return False, "Filename contains path separators"

    # Check for null bytes
    if '\x00' in filename_str:
        return False, "Filename contains null bytes"

    # Check for control characters
    if any(ord(char) < 32 for char in filename_str):
        return False, "Filename contains control characters"

    # Check filename is not just dots
    if filename_str.strip('.') == '':
        return False, "Filename cannot be only dots"

    # Check for safe characters (alphanumeric, underscore, hyphen, dot)
    # This regex allows: letters, digits, underscore, hyphen, and dot
    if not re.match(r'^[a-zA-Z0-9_.\-]+$', filename_str):
        return False, "Filename contains unsafe characters (only alphanumeric, _, -, and . allowed)"

    # Check for valid image extension
    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif']
    has_valid_ext = any(filename_str.lower().endswith(ext) for ext in valid_extensions)

    if not has_valid_ext:
        return False, f"Filename must have a valid image extension: {', '.join(valid_extensions)}"

    # Additional check: make sure there's a name before the extension
    name_without_ext = filename_str.rsplit('.', 1)[0]
    if not name_without_ext or len(name_without_ext) == 0:
        return False, "Filename must have a name before the extension"

    return True, None


def add_image_to_book(endpoint, api_key, book_id, filename):
    """
    Add image metadata to the book's image collection.

    Args:
        endpoint: API endpoint URL
        api_key: API key for authentication
        book_id: The book collection ID
        filename: The image filename (should be pre-validated with is_safe_filename)

    Returns:
        Tuple of (success: bool, response_data: dict)
    """
    url = f"{endpoint}/add_image"
    headers = {
        'x-api-key': api_key,
        'Content-Type': 'application/json'
    }

    today = date.today().strftime("%Y-%m-%d")

    # URL-encode the filename for safe URL construction
    # Using safe='' to encode all special characters except alphanumeric and '_.-'
    url_safe_filename = quote(filename, safe='')

    data = {
        "BookId": book_id,
        "Name": f"{filename} - bulk upload tool - {today}",
        "Url": f"https://resources.drskippy.app/books/{url_safe_filename}",
        "ImageType": "cover-face"
    }

    try:
        response = requests.post(url, json=data, headers=headers, timeout=30)

        if response.status_code == 200:
            return True, response.json()
        else:
            return False, response.json() if response.text else {"error": f"HTTP {response.status_code}"}

    except requests.exceptions.RequestException as e:
        return False, {"error": str(e)}
    except Exception as e:
        return False, {"error": f"Unexpected error: {str(e)}"}


def main():
    """Main function to process command-line arguments and upload images."""
    parser = argparse.ArgumentParser(
        description='Upload images from a directory to the API endpoint',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s /path/to/images
  %(prog)s /path/to/images --recursive
  %(prog)s /path/to/images --extensions jpg,png
  %(prog)s /path/to/images --recursive --extensions jpg,png,gif --verbose
        """
    )

    parser.add_argument('directory', help='Directory containing images to upload')
    parser.add_argument('-r', '--recursive', action='store_true',
                        help='Search subdirectories recursively')
    parser.add_argument('-e', '--extensions', type=str,
                        help='Comma-separated list of file extensions (default: jpg,jpeg,png,gif,bmp,webp,tiff)')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Print detailed output for each file')
    parser.add_argument('--dry-run', action='store_true',
                        help='List files that would be uploaded without actually uploading')

    args = parser.parse_args()

    # Parse extensions if provided
    extensions = None
    if args.extensions:
        extensions = [ext.strip() for ext in args.extensions.split(',')]

    # Get configuration
    print("Loading configuration...")
    endpoint, api_key = get_config()
    print(f"Endpoint: {endpoint}")

    # Get list of image files
    print(f"\nScanning directory: {args.directory}")
    print(f"Recursive: {args.recursive}")
    if extensions:
        print(f"Extensions: {', '.join(extensions)}")

    image_files = get_image_files(args.directory, args.recursive, extensions)

    if not image_files:
        print("\nNo image files found!")
        sys.exit(0)

    print(f"\nFound {len(image_files)} image file(s)")

    if args.dry_run:
        print("\n--- DRY RUN MODE (no files will be uploaded) ---")
        for file_path in image_files:
            print(f"  - {file_path}")
        sys.exit(0)

    # Upload images
    print("\nUploading images...")
    print("-" * 70)

    success_count = 0
    error_count = 0
    associated_count = 0
    skipped_count = 0
    unsafe_filename_count = 0

    for idx, file_path in enumerate(image_files, 1):
        print(f"[{idx}/{len(image_files)}] Uploading: {file_path.name}", end="")

        success, response_data = upload_image(endpoint, api_key, file_path)

        if success:
            success_count += 1
            print(" ✓")
            if args.verbose:
                print(f"    Response: {response_data}")

            # Validate filename for URL safety before associating
            is_valid, error_msg = is_safe_filename(file_path.name)

            if not is_valid:
                unsafe_filename_count += 1
                skipped_count += 1
                print(f"    ⚠ Skipping association (unsafe filename: {error_msg})")
                continue

            # Try to extract book ID and associate image with book
            book_id = extract_book_id(file_path.name)

            if book_id:
                print(f"    Associating with book ID {book_id}...", end="")
                assoc_success, assoc_response = add_image_to_book(
                    endpoint, api_key, book_id, file_path.name
                )

                if assoc_success:
                    associated_count += 1
                    print(" ✓")
                    if args.verbose:
                        print(f"      Association response: {assoc_response}")
                else:
                    print(" ✗")
                    print(f"      Association ERROR: {assoc_response.get('error', 'Unknown error')}")
            else:
                skipped_count += 1
                if args.verbose:
                    print(f"    Skipping association (no book ID found in filename)")
        else:
            error_count += 1
            print(" ✗")
            print(f"    ERROR: {response_data.get('error', 'Unknown error')}")

    # Print summary
    print("-" * 70)
    print(f"\nSummary:")
    print(f"  Total files:           {len(image_files)}")
    print(f"  Successfully uploaded: {success_count}")
    print(f"  Failed uploads:        {error_count}")
    print(f"  Associated with books: {associated_count}")
    print(f"  Skipped association:   {skipped_count}")
    if unsafe_filename_count > 0:
        print(f"    (Unsafe filenames:   {unsafe_filename_count})")

    if error_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
