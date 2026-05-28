# System Design — Wearable Health Signal Processing Pipeline

## Overview

This document describes the end-to-end architecture for ingesting, storing, processing, and scoring wearable health signals from Fitbit Sense devices using AWS-native services.

## Pipeline Stages

This pipeline has two distinct processing paths:

### STREAM PATH (Real-Time)

```
Wearable Device → Producer → Kinesis Data Stream ─┬─→ Firehose → S3 Raw (60s buffer)
                                                   └─→ CloudWatch (custom metrics, live)
```

**Purpose**: Real-time monitoring of health signals as they arrive.

- **Kinesis Data Stream** (`health-pipeline-wearable-stream`): 1 shard, 24-hour retention
- **Firehose Delivery** (`health-pipeline-delivery`): Buffers 60s/5MB, writes to S3 with time-partitioned prefixes (`kinesis/year=YYYY/month=MM/day=DD/`)
- **CloudWatch Custom Metrics**: Producer emits HR, Steps, Skin Temp, Stress Score in real-time for live dashboard
- **Latency**: Seconds (CloudWatch), ~60s (S3 landing)

### BATCH PATH (Scheduled ETL)

```
S3 Raw (new file) → EventBridge (detects S3 event)
                         ↓ (5-min batch window)
                    Glue Workflow
                         ↓
              Crawler (schema discovery) → ETL Job (CSV/JSON → Parquet)
                         ↓
              S3 Processed (partitioned Parquet)
                         ↓
              ┌──────────┴──────────┐
         Athena (SQL)         SageMaker (ML)
              ↓                     ↓
         QuickSight           S3 Curated (Scores)
              ↑_________________________|
```

**Purpose**: Deep analytics, ML scoring, and interactive dashboards.

- **EventBridge Rule**: Triggers on `Object Created` in `kinesis/` prefix, 5-minute batch window
- **Glue Workflow** (`health-pipeline-workflow`): Orchestrates Crawler → ETL
- **Glue Crawler** (`health-pipeline-raw-crawler`): Auto-discovers schema
- **Glue ETL Job** (`health-pipeline-transform`): PySpark — CSV → partitioned Parquet
- **Athena**: Serverless SQL on processed Parquet via Glue Data Catalog
- **SageMaker**: Trains 4 wellness models, writes predictions to curated bucket
- **QuickSight**: 3-sheet interactive dashboard (Overview, Activity, Wellness Trends)
- **Latency**: Minutes (ETL) to hours (ML retraining)

### 2. Data Lake (Storage)

Three-tier S3 architecture:

| Tier | Bucket | Format | Purpose |
|------|--------|--------|---------|
| Raw | `health-pipeline-raw-939295406035` | CSV / JSON | Landing zone, immutable source of truth |
| Processed | `health-pipeline-processed-939295406035` | Parquet (partitioned) | Cleaned, typed, columnar — optimized for queries |
| Curated | `health-pipeline-curated-939295406035` | Parquet | ML feature tables and predicted scores |

- All buckets have `RemovalPolicy.DESTROY` for easy teardown
- Raw also stores Kinesis stream output under `kinesis/` prefix
- LifeSnaps CSV data stored under `lifesnaps/` prefix

### 3. Batch Processing (ETL)

```
S3 (Raw, new file) → EventBridge (S3 event) → Glue Workflow (5-min batch window)
                                                    ↓
                                          Glue Crawler → Glue ETL Job (Spark)
                                                    ↓
                                          S3 (Processed Parquet)
```

- **EventBridge Rule**: Triggers on `Object Created` events in the `kinesis/` prefix of the raw bucket
- **Batch Window**: 5-minute batching — collects events for 5 min before triggering, prevents over-execution
- **Glue Workflow** (`health-pipeline-workflow`): Orchestrates Crawler → ETL in sequence
- **Glue Database**: `health_pipeline_db` — catalog for all tables
- **Glue Crawler** (`health-pipeline-raw-crawler`): Auto-discovers schema from raw CSV files
- **Glue ETL Job** (`health-pipeline-transform`): PySpark job that:
  - Reads raw daily CSV files
  - Casts types (date parsing, string IDs)
  - Adds partition columns (year, month)
  - Writes partitioned Parquet to processed bucket
- **Runtime**: Glue 4.0, 2× G.1X workers (minimal cost)

### 4. Analytics (Query)

```
S3 (Processed) → Athena → SQL results
```

- Athena queries Parquet directly via Glue Data Catalog
- Serverless — pay per query scanned
- Partition pruning on year/month reduces scan cost

### 5. Machine Learning

```
S3 (Processed) → SageMaker Notebook → Trained Model → S3 (Curated Scores)
```

- **Notebook** (`health-pipeline-notebook`): ml.t3.medium, 20GB storage
- **4 target scores** to predict:
  1. Sleep quality (0–100)
  2. Stress/recovery (0–100)
  3. Activity/strain (0–100)
  4. Illness risk (0–100)
- Feature engineering and model training done in notebook
- Trained models produce batch predictions written to curated bucket

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          AWS Account 939295406035                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────┐    ┌──────────┐    ┌──────────────────────┐              │
│  │  Kinesis  │───▶│ Firehose │───▶│  S3 Raw Bucket       │              │
│  │  Stream   │    │          │    │  - kinesis/ (stream)  │              │
│  └──────────┘    └──────────┘    │  - lifesnaps/ (batch) │              │
│       ▲                          └──────────┬───────────┘              │
│       │                                     │                           │
│  ┌──────────┐                    ┌──────────▼───────────┐              │
│  │ Producer  │                    │  Glue Crawler        │              │
│  │ Script    │                    │  (schema discovery)   │              │
│  └──────────┘                    └──────────┬───────────┘              │
│                                             │                           │
│                                  ┌──────────▼───────────┐              │
│                                  │  Glue ETL Job         │              │
│                                  │  (CSV → Parquet)      │              │
│                                  └──────────┬───────────┘              │
│                                             │                           │
│                                  ┌──────────▼───────────┐              │
│                                  │  S3 Processed Bucket  │              │
│                                  │  (Partitioned Parquet)│              │
│                                  └─────┬────────┬───────┘              │
│                                        │        │                       │
│                              ┌─────────▼──┐  ┌──▼──────────┐          │
│                              │   Athena    │  │  SageMaker   │          │
│                              │  (SQL)      │  │  Notebook    │          │
│                              └─────────────┘  └──────┬──────┘          │
│                                                      │                  │
│                                           ┌──────────▼───────────┐     │
│                                           │  S3 Curated Bucket   │     │
│                                           │  (Wellness Scores)   │     │
│                                           └──────────────────────┘     │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Key Architectural Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Storage format | Parquet | Columnar, compressed, partition-friendly — ideal for Athena/Spark |
| Partitioning | year/month | Balances partition count vs. query selectivity for 4-month dataset |
| Stream vs. batch | Both | Kinesis demonstrates real-time capability; bulk CSV upload for actual analysis |
| Glue version | 4.0 | Latest, supports Python 3.10+ and Spark 3.3 |
| Notebook size | ml.t3.medium | Cost-effective for development, can scale up for training |
| Single region | us-east-1 | Personal dev, no HA requirements |

## Cost Considerations

- **Kinesis**: ~$0.36/day (1 shard) — stop stream when not actively demo'ing
- **Glue ETL**: ~$0.44 per run (2 DPUs × ~5 min)
- **SageMaker notebook**: ~$0.05/hr (ml.t3.medium) — **stop when not in use**
- **S3 + Athena**: Negligible for this data volume
- **Estimated monthly**: <$20 if notebook is stopped when idle

## Dataset Schema (LifeSnaps Daily)

Key columns used for wellness scoring:

| Column | Type | Signal |
|--------|------|--------|
| resting_hr | float | Resting heart rate (bpm) |
| hrv_rmssd | float | Heart rate variability |
| sleep_duration | float | Total sleep (minutes) |
| sleep_efficiency | float | % time asleep in bed |
| deep_sleep_minutes | float | Deep sleep stage |
| steps | int | Daily step count |
| active_minutes | int | Active zone minutes |
| stress_score | float | Fitbit stress score |
| spo2_avg | float | Blood oxygen % |
| skin_temp_deviation | float | Relative skin temperature |

## Future Enhancements

- QuickSight dashboard for wellness trend visualization
- SageMaker endpoint for real-time scoring
- Glue Workflow to orchestrate crawler → ETL → model inference
- CloudWatch alarms for pipeline health
