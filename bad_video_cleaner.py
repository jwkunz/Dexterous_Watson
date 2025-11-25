#!/usr/bin/env python3
import argparse
import subprocess
import os
from pathlib import Path
from multiprocessing import Pool, cpu_count
from tqdm import tqdm
import time

VIDEO_EXTS = {".mp4", ".mov", ".avi", ".wmv", ".mkv", ".flv", ".mpeg", ".mpg",".3gp"}

# ------------------------------------------------------------
# VLC test
# ------------------------------------------------------------
def vlc_can_play(path: Path, timeout: int = 30) -> (bool, str):
    """
    Returns (True, "ok") if VLC can play the video.
    Returns (False, reason) if VLC fails.
    """
    try:
        result = subprocess.run(
            ["cvlc", "--intf", "dummy", "--play-and-exit", "--no-sout-video", str(path)],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        if result.returncode != 0:
            return False, result.stderr.strip()
        return True, "ok"
    except subprocess.TimeoutExpired:
        return False, "timeout expired"
    except FileNotFoundError:
        return False, "cvlc not found, please install VLC and ensure 'cvlc' is in PATH"

# ------------------------------------------------------------
# Work unit for multiprocessing
# ------------------------------------------------------------
def check_video(path: str):
    """Check a single video file."""
    playable, reason = vlc_can_play(Path(path))
    return (path, not playable, reason)

# ------------------------------------------------------------
# Main scanning logic
# ------------------------------------------------------------
def scan_videos(directory: Path, workers: int, dry_run: bool, log_path: Path):
    # Collect files
    files = [str(p) for p in directory.rglob("*") if p.suffix.lower() in VIDEO_EXTS]

    if not files:
        print("No video files found.")
        return

    print(f"Scanning {len(files)} video files using {workers} workers...")
    time.sleep(0.5)

    corrupted = []
    good = []

    with Pool(workers) as pool, open(log_path, "w") as log:
        for path, is_corrupt, reason in tqdm(
            pool.imap_unordered(check_video, files),
            total=len(files),
            desc="Checking videos",
        ):
            if is_corrupt:
                print(f"CORRUPT\t{reason}\t{path}\n")
                corrupted.append(path)
                log.write(f"CORRUPT\t{reason}\t{path}\n")
            else:
                good.append(path)
                log.write(f"OK\t{path}\n")
                print(f"OK\t{path}\n")

    print("\n=== Scan Complete ===")
    print(f"Good videos:     {len(good)}")
    print(f"Corrupted videos: {len(corrupted)}")
    print(f"Log written to:   {log_path}")

    if corrupted and not dry_run:
        print("\nDeleting corrupted files...")
        for file in corrupted:
            try:
                os.remove(file)
                print(f"Deleted: {file}")
            except Exception as e:
                print(f"Could not delete {file}: {e}")

    if dry_run:
        print("\nDry run mode: No files deleted.")

# ------------------------------------------------------------
# CLI
# ------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Detect and delete corrupted video files using VLC."
    )
    parser.add_argument(
        "directory",
        type=str,
        help="Directory to scan recursively."
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=cpu_count(),
        help="Number of parallel processes to use."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not delete corrupted videos."
    )
    parser.add_argument(
        "--log",
        type=str,
        default="video_scan.log",
        help="Path to log file."
    )

    args = parser.parse_args()

    scan_videos(
        directory=Path(args.directory),
        workers=args.workers,
        dry_run=args.dry_run,
        log_path=Path(args.log)
    )

if __name__ == "__main__":
    main()
