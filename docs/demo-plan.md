# Live Demo Plan — CISC 525 Final Presentation

## Pre-Demo Setup (before class)
1. Run `ada-personal` to get fresh AWS credentials
2. Ensure producer is NOT running (so we can start it live)
3. Open these tabs in browser:
   - AWS CloudWatch Dashboard: `health-pipeline-streaming`
   - AWS QuickSight Dashboard: `health-pipeline-dashboard`
   - AWS CloudFormation Stacks page (shows infrastructure)
4. Have terminal ready with: `cd ~/w/dev-agent/BigData-projects/health-pipeline`

---

## Demo Flow (10-12 minutes)

### Part 1: Architecture Overview (2 min)
- Show the architecture diagram (slide)
- Explain: "Two paths — stream for real-time monitoring, batch for deep analytics and ML"

### Part 2: Infrastructure as Code (1 min)
- Show CloudFormation stacks page → 4 stacks deployed
- "Everything is defined in CDK Python — one command to deploy, one command to tear down"

### Part 3: Live Streaming Demo (4 min)
- Switch to CloudWatch Dashboard (set to Last 15 min, auto-refresh 10s)
- In terminal, run:
  ```bash
  python src/scripts/producer.py --source local \
    --data-dir data/rais_anonymized/csv_rais_anonymized \
    --delay 0.02 --limit 500
  ```
- Narrate while it runs:
  - "Producer simulates 500 hourly wearable readings being streamed to Kinesis"
  - "Firehose buffers for 60 seconds then delivers to S3"
  - "Custom metrics are pushed to CloudWatch in real-time"
- Watch CloudWatch panels light up:
  - Incoming Records spike
  - Heart Rate, Steps, Skin Temp, Calories populate
- "In production, this would be actual Fitbit/Apple Watch data via IoT Core"

### Part 4: Batch Analytics Dashboard (3 min)
- Switch to QuickSight Dashboard
- **Overview tab**: Show KPIs and charts for all participants
- Select a specific participant from dropdown → all visuals update
- "Each user gets personalized health insights"
- **Activity tab**: Show HR zones pie chart, calories trend, active zone minutes
- **Wellness Trends tab**: Show the 4 ML wellness scores over time
- "These scores are predicted by our GradientBoosting models trained on the processed data"

### Part 5: ML Results (2 min)
- Show model performance table (slide):
  | Score | MAE | R² |
  |-------|-----|-----|
  | Sleep Quality | 0.85 | 0.958 |
  | Stress Recovery | 0.85 | 0.993 |
  | Activity Strain | 0.18 | 0.999 |
  | Illness Risk | 1.21 | 0.985 |
- "All models achieve R² > 0.95 using 52 features from the wearable data"

### Part 6: Automated Pipeline (1 min)
- "When Firehose delivers new data to S3, EventBridge detects it"
- "After a 5-minute batch window, it automatically triggers the Glue Workflow"
- "Crawler discovers schema, ETL converts to Parquet, and QuickSight picks up the new data"
- "Fully automated — no manual intervention needed"

---

## Backup Plan
- If AWS credentials expire mid-demo: show pre-recorded screenshots
- If producer fails: show the CloudWatch data from earlier runs (data persists)
- If QuickSight is slow: show static visualization charts from `docs/figures/`

---

## Key Talking Points to Hit
- **Scale**: 159K hourly records, 71 participants, 35+ signal types
- **Cost**: ~$12/month with notebook stopped
- **Teardown**: Single `cdk destroy --all`
- **Real-time + Batch**: Both paths from same data lake
- **ML**: 4 clinically-informed wellness scores, all R² > 0.95
- **Serverless**: Athena, Glue, Firehose — no servers to manage
