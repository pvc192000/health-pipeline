# Grafana Dashboard

Real-time and historical wellness monitoring dashboard powered by Grafana.

## Panels

| Panel | Data Source | Description |
|-------|-------------|-------------|
| Kinesis Incoming Records/sec | CloudWatch | Live streaming throughput |
| Firehose Delivery (bytes) | CloudWatch | S3 delivery volume |
| Average Resting Heart Rate | Athena | Daily trend across participants |
| Average Daily Steps | Athena | Activity trend over time |
| Wellness Score Distribution | Athena | Predicted scores (4 models) |
| Sleep Duration Trend | Athena | Hours of sleep over time |
| HRV (RMSSD) Trend | Athena | Heart rate variability trend |
| Pipeline Stats | Athena | Total records, participants, avg metrics |

## Setup

### Prerequisites
- Docker installed
- AWS credentials configured (`ada-personal`)

### Run

```bash
cd src/dashboard

# Export AWS credentials for Grafana to use
export AWS_ACCESS_KEY_ID=$(aws configure get aws_access_key_id)
export AWS_SECRET_ACCESS_KEY=$(aws configure get aws_secret_access_key)
export AWS_SESSION_TOKEN=$(aws configure get aws_session_token)

# Start Grafana
docker-compose up -d
```

Open http://localhost:3000 — login with `admin` / `$GRAFANA_PASSWORD`.

The dashboard is auto-provisioned with Athena + CloudWatch data sources.

### Demo Flow

1. Open the Grafana dashboard in the browser
2. In a terminal, run the Kinesis producer:
   ```bash
   python src/scripts/producer.py --source local --data-dir data/rais_anonymized/csv_rais_anonymized --delay 0.1 --limit 0
   ```
3. Watch the Kinesis/Firehose panels update in real-time
4. Historical panels show wellness trends from Athena

### Stop

```bash
docker-compose down
```
