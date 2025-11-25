#!/usr/bin/env python3
"""
List all unique file extensions in a directory tree.

Usage:
    python list_extensions.py <source_dir>

Description:
    Recursively scans <source_dir> for files and prints all unique file
    extensions found, along with a count of how many files have each extension.
    Files without an extension are reported under "no_extension".
"""

import os
import sys
from collections import Counter
from tqdm import tqdm  # optional, for progress bar (pip install tqdm)


def list_file_extensions(source_dir: str):
    if not os.path.isdir(source_dir):
        print(f"Error: '{source_dir}' is not a valid directory.")
        sys.exit(1)

    # Collect file extensions
    ext_counter = Counter()
    total_files = 0

    for root, _, files in os.walk(source_dir):
        for name in files:
            total_files += 1
            _, ext = os.path.splitext(name)
            ext = ext[1:].lower() if ext else "no_extension"
            ext_counter[ext] += 1

    if total_files == 0:
        print("No files found.")
        return

    print(f"\n📂 Scanned {total_files} files total.\n")
    print("File extensions found:\n")
    print(f"{'Extension':<20} {'Count':>10}")
    print("-" * 32)

    for ext, count in sorted(ext_counter.items(), key=lambda x: (-x[1], x[0])):
        print(f"{ext:<20} {count:>10}")

    print("\n✅ Done!")


def main():
    if len(sys.argv) != 2:
        print("Usage: python list_extensions.py <source_dir>")
        sys.exit(1)

    source_dir = sys.argv[1]
    list_file_extensions(source_dir)


if __name__ == "__main__":
    main()
