#!/usr/bin/env python3
"""Helper script to download LifeSnaps dataset and upload to S3 raw bucket.

Usage:
    python data_helper.py download   # Download from Zenodo to local ./data/
    python data_helper.py upload     # Upload ./data/ to S3 raw bucket
"""
import os
import sys
import subprocess

BUCKET = "health-pipeline-raw"
ZENODO_RECORD = "6826682"
LOCAL_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
S3_PREFIX = "lifesnaps/"


def download():
    """Download LifeSnaps CSV files from Zenodo."""
    os.makedirs(LOCAL_DATA_DIR, exist_ok=True)
    print(f"Download the dataset manually from: https://zenodo.org/record/{ZENODO_RECORD}")
    print(f"Place CSV files in: {os.path.abspath(LOCAL_DATA_DIR)}")
    print()
    print("Key files to download:")
    print("  - daily_fitbit_sema_df_*.csv (daily summaries)")
    print("  - hourly_fitbit_sema_df_*.csv (hourly data)")
    print("  - minutely_fitbit_sema_df_*.csv (minute-level data)")


def upload():
    """Upload local data to S3 raw bucket."""
    if not os.path.isdir(LOCAL_DATA_DIR):
        print(f"Error: {LOCAL_DATA_DIR} not found. Run 'download' first.")
        sys.exit(1)

    cmd = [
        "aws", "s3", "sync",
        LOCAL_DATA_DIR,
        f"s3://{BUCKET}/{S3_PREFIX}",
        "--exclude", "*.zip",
        "--exclude", "*.bson",
    ]
    print(f"Uploading to s3://{BUCKET}/{S3_PREFIX} ...")
    subprocess.run(cmd, check=True)
    print("Done.")


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("download", "upload"):
        print(__doc__)
        sys.exit(1)

    if sys.argv[1] == "download":
        download()
    elif sys.argv[1] == "upload":
        upload()
