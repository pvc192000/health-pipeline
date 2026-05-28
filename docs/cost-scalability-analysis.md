# Cost & Scalability Analysis

## Current Pipeline Costs (71 participants, ~22MB raw data)

| Service | Configuration | Monthly Cost | Notes |
|---------|--------------|-------------|-------|
| Kinesis Data Stream | 1 shard | ~$11 | $0.36/day (shard-hour pricing) |
| Kinesis Firehose | Pay per GB | ~$0.01 | Negligible at this scale |
| S3 Storage | ~30MB total | ~$0.001 | Standard tier |
| Glue ETL | 2 DPUs, ~90s/run | ~$0.13/run | $0.44/DPU-hour, billed per second |
| Glue Crawler | On-demand | ~$0.04/run | Same DPU pricing |
| Athena | Pay per scan | ~$0.005/query | $5/TB scanned; Parquet reduces scans |
| SageMaker Notebook | ml.t3.medium | ~$36/month | Only if running 24/7; stop when idle |
| **Total (active)** | | **~$12/month** | With notebook stopped |
| **Total (with notebook)** | | **~$48/month** | Notebook running 24/7 |

## Scaling Projections

### Scenario: 10,000 participants (140× current)

| Service | Scaled Configuration | Estimated Monthly Cost |
|---------|---------------------|----------------------|
| Kinesis | 2-3 shards | ~$25-35 |
| Firehose | ~3GB/day | ~$1 |
| S3 Storage | ~50GB | ~$1.15 |
| Glue ETL | 5-10 DPUs, ~5min/run | ~$2-4/run |
| Athena | Larger scans | ~$0.25/query |
| SageMaker | ml.m5.xlarge for training | ~$70 (training only) |
| **Total** | | **~$100-150/month** |

### Scenario: 1M participants (enterprise scale)

| Service | Scaled Configuration | Estimated Monthly Cost |
|---------|---------------------|----------------------|
| Kinesis | 50+ shards or on-demand mode | ~$500-1000 |
| Firehose | ~300GB/day | ~$90 |
| S3 Storage | ~5TB | ~$115 |
| Glue ETL | 20-50 DPUs | ~$20-50/run |
| Athena | Petabyte-scale | ~$5-25/query |
| SageMaker | ml.p3.2xlarge endpoint | ~$2,200 (real-time) |
| **Total** | | **~$3,000-4,000/month** |

## Architectural Decisions & Tradeoffs

### Storage Format: Parquet vs. CSV

| Metric | CSV (Raw) | Parquet (Processed) | Improvement |
|--------|-----------|--------------------:|------------|
| File size | 22MB | 4MB | 5.5× compression |
| Athena scan cost | $0.11/TB | $0.02/TB | 5× cheaper queries |
| Query speed | ~3s | ~1s | 3× faster |
| Schema evolution | Manual | Native | Built-in support |

### Partitioning Strategy: year/month

- **Chosen**: `year/month` — 8 partitions for 4-month dataset
- **Alternative**: `participant_id/date` — better for per-user queries but 71×120 = 8,520 partitions (too many small files)
- **At scale**: Switch to `year/month/day` with file compaction

### Batch vs. Stream Processing

| Aspect | Batch (Glue ETL) | Stream (Kinesis) |
|--------|-------------------|-----------------|
| Latency | Minutes-hours | Seconds |
| Cost efficiency | Higher (bulk) | Lower per-record |
| Use case | Historical analysis | Real-time alerts |
| Our approach | Primary processing path | Demo + future alerting |

**Decision**: Batch for analytics, stream for demonstrating real-time capability. At scale, would add Kinesis Analytics for real-time anomaly detection (e.g., sudden HR spike → immediate alert).

### ML Model Deployment

| Option | Latency | Cost | When to Use |
|--------|---------|------|-------------|
| Batch inference (current) | Hours | ~$0.13/run | Historical scoring, dashboards |
| SageMaker endpoint | <100ms | ~$70-2200/month | Real-time wellness alerts |
| Lambda + model artifact | <1s | Pay per invoke | Low-traffic API |

**Decision**: Batch inference is sufficient for daily wellness scores. Real-time endpoint only justified at enterprise scale with alerting requirements.

## Cost Optimization Strategies

1. **Stop SageMaker notebook when idle** — saves ~$36/month
2. **Use Kinesis on-demand mode** at scale instead of provisioned shards
3. **Compact small Parquet files** — fewer S3 GET requests
4. **Athena workgroups with byte limits** — prevent runaway queries
5. **S3 Intelligent-Tiering** for raw data that's rarely re-read
6. **Spot instances for Glue** — up to 60% savings on ETL jobs

## Reliability & Fault Tolerance

| Component | Failure Mode | Mitigation |
|-----------|-------------|-----------|
| Kinesis | Shard throttling | Auto-scaling / on-demand mode |
| Firehose | Delivery failure | Automatic retry + error prefix in S3 |
| Glue ETL | Job failure | Glue Workflow retry policy; idempotent writes |
| S3 | Object loss | 99.999999999% durability (11 9's) |
| Athena | Query timeout | Partition pruning; result caching |
