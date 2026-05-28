#!/usr/bin/env python3
"""SageMaker Processing Job script — trains 4 wellness models and writes predictions."""
import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import boto3
import io
import json
import os

PROCESSED_BUCKET = os.environ.get("PROCESSED_BUCKET", "health-pipeline-processed")
CURATED_BUCKET = os.environ.get("CURATED_BUCKET", "health-pipeline-curated")
REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")


def compute_targets(df):
    df["sleep_quality_score"] = np.clip(
        0.4 * np.clip(df["sleep_duration"].fillna(0) / 480000 * 100, 0, 100)
        + 0.3 * np.clip(df["sleep_efficiency"].fillna(0) * 100, 0, 100)
        + 0.3 * np.clip(df["sleep_deep_ratio"].fillna(0) * 100, 0, 100), 0, 100)
    df["stress_recovery_score"] = np.clip(
        0.4 * np.clip(df["rmssd"].fillna(30) / 80 * 100, 0, 100)
        + 0.3 * np.clip((80 - df["resting_hr"].fillna(70)) / 20 * 100, 0, 100)
        + 0.3 * np.clip(100 - df["stress_score"].fillna(50), 0, 100), 0, 100)
    df["activity_strain_score"] = np.clip(
        0.5 * np.clip(df["steps"].fillna(0) / 10000 * 100, 0, 100)
        + 0.5 * np.clip((df["lightly_active_minutes"].fillna(0) + df["moderately_active_minutes"].fillna(0)
                         + df["very_active_minutes"].fillna(0)) / 60 * 100, 0, 100), 0, 100)
    df["illness_risk_score"] = np.clip(
        0.4 * np.clip((97 - df["spo2"].fillna(97)) / 3 * 100, 0, 100)
        + 0.3 * np.clip(abs(df["daily_temperature_variation"].fillna(0)) / 2 * 100, 0, 100)
        + 0.3 * np.clip((df["resting_hr"].fillna(60) - 60) / 20 * 100, 0, 100), 0, 100)
    return df


if __name__ == "__main__":
    print("Loading processed Parquet from S3...")
    s3 = boto3.client("s3", region_name=REGION)
    paginator = s3.get_paginator("list_objects_v2")
    frames = []
    for page in paginator.paginate(Bucket=PROCESSED_BUCKET, Prefix="daily_summaries/"):
        for obj in page.get("Contents", []):
            if obj["Key"].endswith(".parquet"):
                body = s3.get_object(Bucket=PROCESSED_BUCKET, Key=obj["Key"])["Body"].read()
                frames.append(pd.read_parquet(io.BytesIO(body)))
    df = pd.concat(frames, ignore_index=True)
    print(f"Loaded {len(df)} rows")

    df = compute_targets(df)
    target_cols = ["sleep_quality_score", "stress_recovery_score", "activity_strain_score", "illness_risk_score"]
    meta_cols = ["date", "participant_id", "id", "year", "month"]
    feature_cols = [c for c in df.select_dtypes(include=[np.number]).columns if c not in target_cols + meta_cols]

    df_model = df[feature_cols + target_cols].dropna(thresh=len(feature_cols) * 0.5)
    df_model = df_model.fillna(df_model.median())
    print(f"Training on {len(df_model)} rows, {len(feature_cols)} features")

    results = {}
    for target in target_cols:
        X = df_model[feature_cols]
        y = df_model[target]
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        model = GradientBoostingRegressor(n_estimators=100, max_depth=4, random_state=42)
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        results[target] = {"model": model, "mae": mae, "r2": r2}
        print(f"  {target}: MAE={mae:.2f}, R²={r2:.3f}")

    # Batch inference
    X_all = df_model[feature_cols]
    score_df = pd.DataFrame()
    score_df["participant_id"] = df.loc[df_model.index, "participant_id"].values
    score_df["date"] = df.loc[df_model.index, "date"].values
    for target in target_cols:
        score_df[target.replace("_score", "_predicted")] = results[target]["model"].predict(X_all)

    buf = io.BytesIO()
    score_df.to_parquet(buf, index=False)
    buf.seek(0)
    s3.put_object(Bucket=CURATED_BUCKET, Key="wellness_scores/scores.parquet", Body=buf.getvalue())
    print(f"Wrote {len(score_df)} predictions to s3://{CURATED_BUCKET}/wellness_scores/")

    # Save metrics
    metrics = {name: {"mae": r["mae"], "r2": r["r2"]} for name, r in results.items()}
    s3.put_object(Bucket=CURATED_BUCKET, Key="wellness_scores/metrics.json",
                  Body=json.dumps(metrics, indent=2).encode())
    print("Done.")
