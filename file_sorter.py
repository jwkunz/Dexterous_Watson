#!/usr/bin/env python3
"""
Sort recovered files by extension.

Usage:
    python sort_by_extension.py <source_dir> <destination_dir>

Description:
    Recursively scans <source_dir> for files.
    For each file found, copies it into a subdirectory of <destination_dir>
    named after the file's extension (without the leading dot).
    Files without an extension are placed in a folder called "no_extension".
    A progress bar shows progress.
"""

import os
import sys
import shutil
from tqdm import tqdm  # pip install tqdm

def sort_files_by_extension(source_dir: str, dest_dir: str):
    # Collect all file paths
    all_files = []
    for root, _, files in os.walk(source_dir):
        for name in files:
            full_path = os.path.join(root, name)
            all_files.append(full_path)

    if not all_files:
        print("No files found in source directory.")
        return

    # Iterate with a progress bar
    for src_path in tqdm(all_files, desc="Sorting files", unit="file"):
        # Determine extension (without dot)
        _, ext = os.path.splitext(src_path)
        ext_folder = ext[1:].lower() if ext else "no_extension"

        # Create target folder
        target_folder = os.path.join(dest_dir, ext_folder)
        os.makedirs(target_folder, exist_ok=True)

        # Copy file to destination folder
        dest_path = os.path.join(target_folder, os.path.basename(src_path))

        # If a file with the same name exists, avoid overwrite by renaming
        base, ext2 = os.path.splitext(dest_path)
        counter = 1
        while os.path.exists(dest_path):
            dest_path = f"{base}_{counter}{ext2}"
            counter += 1

        shutil.copy2(src_path, dest_path)

    print(f"\n✅ Sorting complete! Files organized in: {dest_dir}")


def main():
    if len(sys.argv) != 3:
        print("Usage: python sort_by_extension.py <source_dir> <destination_dir>")
        sys.exit(1)

    source_dir = sys.argv[1]
    dest_dir = sys.argv[2]

    if not os.path.isdir(source_dir):
        print(f"Error: Source directory '{source_dir}' does not exist or is not a directory.")
        sys.exit(1)

    os.makedirs(dest_dir, exist_ok=True)
    sort_files_by_extension(source_dir, dest_dir)


if __name__ == "__main__":
    main()
