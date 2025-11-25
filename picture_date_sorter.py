#!/usr/bin/env python3
"""
Advanced Photo Organizer

New features added:
  ✓ Support for more formats: JPEG, TIFF, HEIC/HEIF, PNG, BMP, SVG, RAW (.CR2, .NEF, .ARW, .DNG)
  ✓ Recursive directory scanning
  ✓ EXIF extraction fallback using exiftool (if installed)
  ✓ PNG metadata parsing (tEXt chunks)
  ✓ SVG metadata parsing (Dublin Core date)
  ✓ Full report CSV of all moved files
  ✓ Dry‑run mode
  ✓ Progress bar

Requires:
  pip install pillow tqdm pillow-heif exifread
  (Optional) apt install exiftool
"""

import os
import shutil
import csv
import subprocess
from pathlib import Path
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS
from pillow_heif import register_heif_opener
import exifread
from tqdm import tqdm

register_heif_opener()

SUPPORTED_EXT = {
    ".gif",
    ".jpg", ".jpeg", ".png", ".bmp", ".svg", ".tif", ".tiff",
    ".heic", ".heif", ".cr2", ".cr3", ".nef", ".arw", ".dng"
}


def extract_exif_pillow(path: Path):
    """Try extracting EXIF using Pillow."""
    try:
        img = Image.open(path)
        exif = img.getexif()
        if not exif:
            return None
        for tag_id, value in exif.items():
            tag = TAGS.get(tag_id, tag_id)
            if tag in ("DateTimeOriginal", "DateTimeDigitized", "DateTime"):
                try:
                    return datetime.strptime(str(value), "%Y:%m:%d %H:%M:%S")
                except Exception:
                    pass
    except Exception:
        pass
    return None


def extract_exif_exifread(path: Path):
    """Try extracting EXIF using exifread (better RAW support)."""
    try:
        with open(path, "rb") as f:
            tags = exifread.process_file(f, details=False)
        for key in ("EXIF DateTimeOriginal", "Image DateTime"):
            if key in tags:
                val = str(tags[key])
                try:
                    return datetime.strptime(val, "%Y:%m:%d %H:%M:%S")
                except Exception:
                    pass
    except Exception:
        pass
    return None


def extract_exif_exiftool(path: Path):
    """Try calling exiftool if installed."""
    try:
        result = subprocess.run(
            ["exiftool", "-DateTimeOriginal", "-j", str(path)],
            capture_output=True, text=True
        )
        if result.returncode == 0 and "DateTimeOriginal" in result.stdout:
            import json
            data = json.loads(result.stdout)[0]
            if "DateTimeOriginal" in data:
                dt = data["DateTimeOriginal"].replace(":", "-", 2)
                return datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
    except Exception:
        pass
    return None


def extract_png_date(path: Path):
    """Check png metadata chunks for creation time."""
    try:
        img = Image.open(path)
        info = img.info
        for key in ("creation_time", "date", "timestamp"):
            if key in info:
                try:
                    return datetime.fromisoformat(info[key])
                except Exception:
                    pass
    except Exception:
        pass
    return None


def extract_svg_date(path: Path):
    """Extract Dublin Core date from SVG metadata if present."""
    try:
        text = path.read_text(errors="ignore")
        import re
        match = re.search(r"<dc:date>(.*?)</dc:date>", text)
        if match:
            try:
                return datetime.fromisoformat(match.group(1))
            except Exception:
                pass
    except Exception:
        pass
    return None


def get_datetime(path: Path):
    """Try all methods to extract a date."""
    for func in (
        extract_exif_pillow,
        extract_exif_exifread,
        extract_exif_exiftool,
        extract_png_date,
        extract_svg_date,
    ):
        dt = func(path)
        if dt:
            return dt
    return None



def organize_photos(source_dir: str, dry_run=False, spread=False, verbose=False):
    source = Path(source_dir)
    report_path = source / "photo_organizer_report.csv"

    all_files = [f for f in source.rglob("*") if f.is_file() and f.suffix.lower() in SUPPORTED_EXT]

    with open(report_path, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["file", "target", "date", "status"])

        for f in tqdm(all_files, desc="Organizing", unit="file"):
            dt = get_datetime(f)

            if dt:
                folder = f"{dt.year:04d}-{dt.month:02d}"
                target_dir = source / folder
                if spread:
                    target_dir = get_spread_subfolder(target_dir)
            else:
                target_dir = source / "unknown_date"
                if spread:
                    target_dir = get_spread_subfolder(target_dir)

            target_dir.mkdir(exist_ok=True)
            target_path = target_dir / f.name

            # Avoid overwriting
            if target_path.exists():
                stem, suf = target_path.stem, target_path.suffix
                c = 1
                while (target_dir / f"{stem}_{c}{suf}").exists():
                    c += 1
                target_path = target_dir / f"{stem}_{c}{suf}"

            if not dry_run:
                shutil.move(str(f), str(target_path))

            writer.writerow([str(f), str(target_path), dt, "moved" if not dry_run else "dry_run"])

    if verbose:
        print(f"Done. Report saved to {report_path}")


def get_spread_subfolder(base_dir: Path, max_files=500):
    """Return a subfolder with suffix _#, ensuring none exceed max_files."""
    c = 0
    while True:
        sub = base_dir.parent / f"{base_dir.name}_{c}"
        if not sub.exists():
            return sub
        # Count files
        num = sum(1 for _ in sub.glob("*"))
        if num < max_files:
            return sub
        c += 1


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Organize photos by metadata.")
    parser.add_argument("source", help="Directory containing images")
    parser.add_argument("--dry-run", action="store_true", help="Do not move files")
    parser.add_argument("--spread", action="store_true", help="Distribute files into _# subfolders when a folder exceeds 500 items")
    parser.add_argument("--verbose", action="store_true", help="Print extra information (default shows only progress bar)")
    args = parser.parse_args()

    organize_photos(args.source, dry_run=args.dry_run, spread=args.spread, verbose=args.verbose)
