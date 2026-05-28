#!/usr/bin/env python3
"""Generate visualization charts for the health pipeline project."""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import boto3
import io
import os

PROCESSED_BUCKET = "health-pipeline-processed"
CURATED_BUCKET = "health-pipeline-curated"
REGION = "us-east-1"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "figures")


def load_data():
    s3 = boto3.client("s3", region_name=REGION)
    paginator = s3.get_paginator("list_objects_v2")
    frames = []
    for page in paginator.paginate(Bucket=PROCESSED_BUCKET, Prefix="daily_summaries/"):
        for obj in page.get("Contents", []):
            if obj["Key"].endswith(".parquet"):
                body = s3.get_object(Bucket=PROCESSED_BUCKET, Key=obj["Key"])["Body"].read()
                frames.append(pd.read_parquet(io.BytesIO(body)))
    return pd.concat(frames, ignore_index=True)


def load_scores():
    s3 = boto3.client("s3", region_name=REGION)
    body = s3.get_object(Bucket=CURATED_BUCKET, Key="wellness_scores/scores.parquet")["Body"].read()
    return pd.read_parquet(io.BytesIO(body))


def plot_participant_activity(df):
    """Daily steps distribution by participant."""
    fig, ax = plt.subplots(figsize=(12, 5))
    participant_steps = df.groupby("participant_id")["steps"].mean().dropna().sort_values(ascending=False)
    ax.bar(range(len(participant_steps)), participant_steps.values, color="steelblue")
    ax.set_xlabel("Participant (ranked)")
    ax.set_ylabel("Average Daily Steps")
    ax.set_title("Average Daily Steps by Participant")
    ax.axhline(y=10000, color="green", linestyle="--", alpha=0.7, label="10K goal")
    ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "participant_activity.png"), dpi=150)
    plt.close()


def plot_sleep_patterns(df):
    """Sleep metrics over time."""
    df_sleep = df[["date", "sleep_duration", "sleep_efficiency", "resting_hr"]].dropna()
    df_sleep = df_sleep.sort_values("date")
    weekly = df_sleep.set_index("date").resample("W").mean()

    fig, axes = plt.subplots(3, 1, figsize=(12, 8), sharex=True)

    axes[0].plot(weekly.index, weekly["sleep_duration"] / 60000, color="purple")
    axes[0].set_ylabel("Sleep (hours)")
    axes[0].set_title("Weekly Average Sleep Metrics Across All Participants")
    axes[0].axhline(y=8, color="green", linestyle="--", alpha=0.5)

    axes[1].plot(weekly.index, weekly["sleep_efficiency"] * 100, color="teal")
    axes[1].set_ylabel("Sleep Efficiency (%)")

    axes[2].plot(weekly.index, weekly["resting_hr"], color="red")
    axes[2].set_ylabel("Resting HR (bpm)")
    axes[2].set_xlabel("Date")

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "sleep_patterns.png"), dpi=150)
    plt.close()


def plot_wellness_scores(scores):
    """Distribution of predicted wellness scores."""
    fig, axes = plt.subplots(2, 2, figsize=(10, 8))
    score_cols = scores.columns.tolist()
    colors = ["#2196F3", "#4CAF50", "#FF9800", "#F44336"]

    for ax, col, color in zip(axes.flat, score_cols, colors):
        ax.hist(scores[col].dropna(), bins=30, color=color, alpha=0.7, edgecolor="white")
        ax.set_title(col.replace("_predicted", "").replace("_", " ").title())
        ax.set_xlabel("Score (0-100)")
        ax.set_ylabel("Count")
        ax.axvline(scores[col].mean(), color="black", linestyle="--", alpha=0.7)

    plt.suptitle("Distribution of Predicted Wellness Scores", fontsize=14)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "wellness_scores_distribution.png"), dpi=150)
    plt.close()


def plot_correlation_heatmap(df):
    """Correlation between key health signals."""
    cols = ["resting_hr", "rmssd", "steps", "sleep_duration", "stress_score",
            "spo2", "calories", "sleep_efficiency"]
    cols = [c for c in cols if c in df.columns]
    corr = df[cols].corr()

    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(corr, cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(len(cols)))
    ax.set_yticks(range(len(cols)))
    ax.set_xticklabels(cols, rotation=45, ha="right", fontsize=9)
    ax.set_yticklabels(cols, fontsize=9)
    plt.colorbar(im, ax=ax)
    ax.set_title("Correlation Between Health Signals")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "correlation_heatmap.png"), dpi=150)
    plt.close()


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("Loading data...")
    df = load_data()
    df["date"] = pd.to_datetime(df["date"])
    scores = load_scores()

    print("Generating participant activity chart...")
    plot_participant_activity(df)

    print("Generating sleep patterns chart...")
    plot_sleep_patterns(df)

    print("Generating wellness scores distribution...")
    plot_wellness_scores(scores)

    print("Generating correlation heatmap...")
    plot_correlation_heatmap(df)

    print(f"Done! Charts saved to {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
