#!/usr/bin/env python3
"""Kinesis producer — simulates real-time wearable data by replaying LifeSnaps records.

Reads CSV files from S3 (or local) and sends records one-by-one to the Kinesis stream
with a configurable delay to simulate real-time ingestion.

Usage:
    python producer.py --source local --data-dir ../../data
    python producer.py --source s3 --bucket health-pipeline-raw --prefix lifesnaps/
"""
import argparse
import json
import time
import csv
import io
import boto3

STREAM_NAME = "health-pipeline-wearable-stream"
REGION = "us-east-1"


def send_records(records: list[dict], delay: float):
    """Send records to Kinesis with a delay between each."""
    kinesis = boto3.client("kinesis", region_name=REGION)
    cloudwatch = boto3.client("cloudwatch", region_name=REGION)
    sent = 0

    for record in records:
        kinesis.put_record(
            StreamName=STREAM_NAME,
            Data=json.dumps(record).encode("utf-8"),
            PartitionKey=record.get("id", "default"),
        )
        sent += 1

        # Emit health metrics to CloudWatch every 10 records
        if sent % 10 == 0:
            metrics = []
            participant = record.get("id", "unknown")
            hr = record.get("resting_hr") or record.get("bpm")
            if hr:
                try:
                    metrics.append({"MetricName": "HeartRate", "Value": float(hr), "Unit": "Count", "Dimensions": [{"Name": "Participant", "Value": participant}]})
                except (ValueError, TypeError):
                    pass
            steps_val = record.get("steps")
            if steps_val:
                try:
                    metrics.append({"MetricName": "Steps", "Value": float(steps_val), "Unit": "Count", "Dimensions": [{"Name": "Participant", "Value": participant}]})
                except (ValueError, TypeError):
                    pass
            hrv = record.get("rmssd") or record.get("scl_avg")
            if hrv:
                try:
                    metrics.append({"MetricName": "HRV_RMSSD", "Value": float(hrv), "Unit": "Count", "Dimensions": [{"Name": "Participant", "Value": participant}]})
                except (ValueError, TypeError):
                    pass
            stress = record.get("calories")
            if stress:
                try:
                    metrics.append({"MetricName": "Calories", "Value": float(stress), "Unit": "Count", "Dimensions": [{"Name": "Participant", "Value": participant}]})
                except (ValueError, TypeError):
                    pass
            temp = record.get("temperature") or record.get("nightly_temperature")
            if temp:
                try:
                    metrics.append({"MetricName": "SkinTemperature", "Value": float(temp), "Unit": "Count", "Dimensions": [{"Name": "Participant", "Value": participant}]})
                except (ValueError, TypeError):
                    pass
            if metrics:
                # Also emit without dimension for aggregate dashboard view
                aggregate_metrics = [{"MetricName": m["MetricName"], "Value": m["Value"], "Unit": m["Unit"]} for m in metrics]
                cloudwatch.put_metric_data(Namespace="HealthPipeline/WearableData", MetricData=metrics + aggregate_metrics)

        if sent % 100 == 0:
            print(f"  Sent {sent} records...")
        time.sleep(delay)

    print(f"Done. Sent {sent} total records.")


def load_from_local(data_dir: str) -> list[dict]:
    """Load CSV records from local data directory."""
    import glob
    import os

    records = []
    # Prefer hourly data for richer streaming demo
    hourly = os.path.join(data_dir, "hourly_fitbit_sema_df_unprocessed.csv")
    if os.path.exists(hourly):
        print(f"Loading {os.path.basename(hourly)}...")
        with open(hourly, "r") as f:
            reader = csv.DictReader(f)
            records.extend(list(reader))
        return records

    for csv_file in sorted(glob.glob(os.path.join(data_dir, "daily_fitbit_sema_df_*.csv"))):
        print(f"Loading {os.path.basename(csv_file)}...")
        with open(csv_file, "r") as f:
            reader = csv.DictReader(f)
            records.extend(list(reader))
    return records


def load_from_s3(bucket: str, prefix: str) -> list[dict]:
    """Load CSV records from S3."""
    s3 = boto3.client("s3", region_name=REGION)
    records = []

    response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
    for obj in response.get("Contents", []):
        if "daily_fitbit_sema_df" in obj["Key"] and obj["Key"].endswith(".csv"):
            print(f"Loading s3://{bucket}/{obj['Key']}...")
            body = s3.get_object(Bucket=bucket, Key=obj["Key"])["Body"].read().decode("utf-8")
            reader = csv.DictReader(io.StringIO(body))
            records.extend(list(reader))
    return records


def main():
    parser = argparse.ArgumentParser(description="Kinesis wearable data producer")
    parser.add_argument("--source", choices=["local", "s3"], default="local")
    parser.add_argument("--data-dir", default="../../data", help="Local data directory")
    parser.add_argument("--bucket", default="health-pipeline-raw")
    parser.add_argument("--prefix", default="lifesnaps/")
    parser.add_argument("--delay", type=float, default=0.01, help="Seconds between records")
    parser.add_argument("--limit", type=int, default=1000, help="Max records to send (0=all)")
    args = parser.parse_args()

    if args.source == "local":
        records = load_from_local(args.data_dir)
    else:
        records = load_from_s3(args.bucket, args.prefix)

    if not records:
        print("No records found. Check your data source.")
        return

    if args.limit > 0:
        records = records[: args.limit]

    print(f"Sending {len(records)} records to {STREAM_NAME} (delay={args.delay}s)...")
    send_records(records, args.delay)


if __name__ == "__main__":
    main()
