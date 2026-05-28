# AI Platform Comparison

## Can this project be replaced by an AI/no-code platform?

We evaluated whether platforms like Google Opal, AWS App Studio, Microsoft Power Platform, n8n, and Zapier could replace our custom pipeline design.

## Short Answer: Partially, but not fully.

Low-code platforms can handle **some** components (dashboards, simple ETL) but **cannot** replace the full architecture due to limitations in streaming, ML customization, and data scale.

---

## Comparison Table

| Capability | Our Design (AWS Native) | AI/No-Code Platforms |
|-----------|------------------------|---------------------|
| **Real-time streaming ingestion** | Kinesis + Firehose (sub-second) | ❌ Most don't support real-time streams. Zapier/n8n are webhook-based (event-driven, not streaming). Power Platform has limited streaming via Event Hubs but not at this granularity. |
| **Large-scale ETL (159K+ rows, Spark)** | AWS Glue (distributed PySpark) | ⚠️ Power Platform Dataflows handle ~100K rows. n8n/Zapier choke on large datasets. Google Opal is analytics-focused, not ETL. |
| **Custom ML models** | SageMaker + scikit-learn (full control over features, algorithms, hyperparameters) | ⚠️ AutoML options exist (Power Platform AI Builder, AWS App Studio) but limited to pre-built model types. Cannot implement custom composite wellness scores with domain-specific feature engineering. |
| **Columnar storage + partitioning** | S3 Parquet, partitioned by date | ❌ No-code platforms abstract storage. No control over format, partitioning, or cost optimization. |
| **Serverless SQL analytics** | Athena (pay per query, petabyte-scale) | ⚠️ Power BI/Looker offer SQL but limited scale. No partition pruning optimization. |
| **Interactive dashboards** | QuickSight (per-user filtering) | ✅ Power BI, Looker, Google Opal excel here. This is their strength. |
| **Infrastructure as Code** | CDK (reproducible, version-controlled) | ❌ Platforms are click-to-configure. No git history, no reproducibility, no teardown command. |
| **Cost control** | ~$12/month, full teardown | ⚠️ Platforms often charge per user/month ($20-100/user). Less control over underlying compute costs. |
| **Real-time monitoring** | CloudWatch custom metrics + dashboard | ⚠️ Limited. Most platforms don't expose infrastructure-level metrics. |

---

## Platform-Specific Analysis

### Google Opal
- **Strengths**: Natural language queries on data, AI-powered insights
- **Limitations**: No streaming ingestion, no custom ML models, no Spark ETL, tied to Google ecosystem
- **Verdict**: Could replace QuickSight dashboard layer only

### AWS App Studio
- **Strengths**: Low-code app builder within AWS
- **Limitations**: Designed for CRUD apps, not data pipelines. No Kinesis/Glue integration. No ML training.
- **Verdict**: Not applicable to this use case

### Microsoft Power Platform (Power Automate + Power BI + AI Builder)
- **Strengths**: Best dashboard/BI tool, some ML via AI Builder, Dataflows for ETL
- **Limitations**: Dataflows limited to ~100K rows. AI Builder only supports classification/prediction with pre-built templates. No streaming. No Parquet/partitioning control.
- **Verdict**: Could replace batch analytics + dashboard (50% of project) but not streaming or custom ML

### n8n / Zapier
- **Strengths**: Workflow automation, webhook triggers, 1000+ integrations
- **Limitations**: Not designed for data pipelines. No large dataset processing. No ML. Webhook-based (not streaming). Row-by-row processing is prohibitively slow at 159K rows.
- **Verdict**: Could trigger the Glue workflow (replace EventBridge) but nothing else

---

## What CANNOT be replaced

1. **Real-time streaming at scale** — Kinesis handles thousands of records/sec continuously. No-code platforms are request/response, not stream-oriented.

2. **Custom ML with domain expertise** — Our wellness scores use clinically-informed feature engineering (sleep stage ratios, HRV-based stress recovery, SpO2-informed illness risk). AutoML platforms cannot encode this domain knowledge.

3. **Storage format optimization** — Parquet columnar format with date partitioning reduces query costs 5.5×. Platforms abstract this away, resulting in higher costs at scale.

4. **Full pipeline observability** — CloudWatch gives real-time visibility into every pipeline component. No-code platforms are black boxes.

5. **Reproducibility and teardown** — CDK lets us deploy/destroy the entire infrastructure in one command. Critical for academic projects and cost control.

---

## Conclusion

AI platforms excel at **visualization and simple workflows** but fall short for **big data pipelines** that require:
- Sub-second streaming ingestion
- Distributed processing (Spark)
- Custom ML with domain-specific feature engineering
- Storage optimization for cost efficiency
- Full infrastructure control and observability

Our hybrid approach — using managed AWS services with custom code — provides the best balance of **scalability, customization, cost control, and reproducibility** that no single AI platform can match today.

A practical middle ground: Use **Power BI or QuickSight** for the dashboard layer (as we do), while keeping the pipeline backbone (Kinesis, Glue, SageMaker) as custom infrastructure.
