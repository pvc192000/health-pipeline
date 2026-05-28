# Cloud-Native Big Data Pipeline for Wearable Health Signal Processing

End-to-end AWS-native pipeline that ingests wearable device data, processes it through a data lake, and applies ML models to derive wellness insight scores.

## Architecture

Two processing paths from a shared data lake:

**STREAM PATH (Real-Time):**
```
Producer → Kinesis Stream → Firehose → S3 Raw
                 └→ CloudWatch Dashboard (live HR, Steps, Temp)
```

**BATCH PATH (Scheduled ETL):**
```
S3 Raw (new data) → EventBridge (5-min batch) → Glue Workflow (Crawler → ETL)
    → S3 Processed (Parquet) → Athena / SageMaker → QuickSight Dashboard
```

**Stacks:**
| Stack | Resources |
|-------|-----------|
| DataLake | S3 buckets (raw, processed, curated) |
| Ingestion | Kinesis stream + Firehose delivery |
| Processing | Glue database, crawler, ETL job |
| ML | SageMaker notebook instance |

## Dataset

**LifeSnaps** — 71 participants, 71M+ rows, 4 months of Fitbit Sense data.
- Source: https://doi.org/10.5281/zenodo.6826682
- 35+ signal types: HR, HRV, sleep stages, steps, SpO2, EDA, skin temp, stress, VO2max

## Prerequisites

- Python 3.9+
- AWS CDK CLI (`npm install -g aws-cdk`)
- AWS credentials configured (account: 939295406035, region: us-east-1)

## Setup

```bash
cd health-pipeline
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Deploy

```bash
cdk bootstrap aws://939295406035/us-east-1   # first time only
cdk deploy --all
```

## Load Data

```bash
python src/scripts/data_helper.py download   # instructions to get LifeSnaps
python src/scripts/data_helper.py upload     # sync to S3 raw bucket
```

## Teardown

```bash
cdk destroy --all
```

All buckets use `RemovalPolicy.DESTROY` with `auto_delete_objects=True` so teardown is clean.

## Documentation

- [System Design & Pipeline Architecture](docs/system-design.md) — detailed data flow, decisions, cost analysis
- [Cost & Scalability Analysis](docs/cost-scalability-analysis.md) — pricing, scaling projections, tradeoffs

## Results

### Pipeline Verification
- **7,410 daily records** from 71 participants successfully processed
- **Avg resting HR**: 66 bpm | **Avg daily steps**: 8,262
- Kinesis → Firehose → S3 streaming verified (200 records, <60s delivery)

### ML Model Performance
| Score | MAE | R² |
|-------|-----|-----|
| Sleep Quality | 0.85 | 0.958 |
| Stress/Recovery | 0.85 | 0.993 |
| Activity/Strain | 0.18 | 0.999 |
| Illness Risk | 1.21 | 0.985 |

### Visualizations
See `docs/figures/` for generated charts:
- Participant activity distribution
- Sleep pattern trends
- Wellness score distributions
- Health signal correlation heatmap

## Project Structure

```
health-pipeline/
├── app.py                              # CDK entry point
├── cdk.json                            # CDK config
├── requirements.txt                    # Python dependencies
├── infrastructure/                     # CDK stacks
│   ├── data_lake_stack.py             # S3 buckets (raw/processed/curated)
│   ├── ingestion_stack.py             # Kinesis + Firehose
│   ├── processing_stack.py            # Glue DB, crawler, ETL job
│   └── ml_stack.py                    # SageMaker notebook
├── src/
│   ├── etl/transform.py              # Glue Spark ETL (CSV → Parquet)
│   ├── notebooks/wellness_scoring.ipynb  # Interactive ML notebook
│   ├── queries/sample_queries.sql     # Athena verification queries
│   └── scripts/
│       ├── batch_scoring.py           # Local ML training + S3 inference
│       ├── data_helper.py             # Dataset download/upload
│       ├── generate_visualizations.py # Chart generation
│       └── producer.py                # Kinesis stream producer
└── docs/
    ├── system-design.md               # Architecture documentation
    ├── cost-scalability-analysis.md   # Cost & scaling analysis
    └── figures/                        # Generated visualization charts
```

## Team

- Param Chokshi
- Xiukun Hu

## Changelog

| Date | Change |
|------|--------|
| 2026-05-27 | Initial project scaffolding — CDK stacks (DataLake, Ingestion, Processing, ML), ETL script, data helper, README |
| 2026-05-27 | Added system-design.md, implementation plan, SageMaker set to deploy stopped |
| 2026-05-27 | Deployed all 4 stacks to account 939295406035. Added Kinesis producer, ML notebook, sample Athena queries |
| 2026-05-28 | Full pipeline run: data uploaded, ETL succeeded (7410 rows → Parquet), Athena verified, Kinesis/Firehose streaming verified |
| 2026-05-28 | ML models trained (all R² > 0.95), predictions written to curated bucket, visualizations generated |
| 2026-05-28 | Glue Workflow orchestration created, cost/scalability analysis written, final README update |
| 2026-05-28 | Added Grafana dashboard (docker-compose) with CloudWatch + Athena data sources, 8 panels |
| 2026-05-28 | QuickSight: consolidated 3-sheet dashboard (Overview, Activity, Wellness) with participant + date filters |
| 2026-05-28 | EventBridge auto-trigger: S3 new data → 5-min batch → Glue Workflow. Updated architecture diagram |
