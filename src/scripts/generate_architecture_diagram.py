#!/usr/bin/env python3
"""Generate pipeline architecture diagram - simplified to avoid overlapping arrows."""
from diagrams import Diagram, Cluster, Edge
from diagrams.aws.analytics import KinesisDataStreams, KinesisDataFirehose, GlueCrawlers, GlueDataCatalog, Athena, Quicksight
from diagrams.aws.storage import S3
from diagrams.aws.ml import Sagemaker
from diagrams.aws.management import Cloudwatch
from diagrams.aws.integration import Eventbridge
import os

output_dir = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "figures")
os.makedirs(output_dir, exist_ok=True)

with Diagram(
    "Wearable Health Pipeline",
    filename=os.path.join(output_dir, "pipeline_architecture"),
    show=False,
    direction="LR",
    graph_attr={"fontsize": "16", "pad": "0.8", "nodesep": "0.8", "ranksep": "1.5"},
):

    with Cluster("Stream Path (Real-Time)", graph_attr={"bgcolor": "#fff3e0", "style": "rounded"}):
        producer = KinesisDataStreams("Producer\n(Simulator)")
        stream = KinesisDataStreams("Kinesis\nStream")
        firehose = KinesisDataFirehose("Firehose")
        cloudwatch = Cloudwatch("CloudWatch\nDashboard")

        producer >> stream >> firehose
        stream >> Edge(label="live metrics", style="dashed") >> cloudwatch

    raw = S3("S3 Raw Bucket\n(Landing Zone)")
    firehose >> Edge(label="60s buffer") >> raw

    with Cluster("Batch Path (Scheduled ETL)", graph_attr={"bgcolor": "#e3f2fd", "style": "rounded"}):
        eventbridge = Eventbridge("EventBridge\n(5-min batch)")
        crawler = GlueCrawlers("Glue Crawler")
        glue_etl = GlueCrawlers("Glue ETL\n(Spark)")
        processed = S3("S3 Processed\n(Parquet)")

        eventbridge >> crawler >> glue_etl >> processed

    raw >> Edge(label="new data event") >> eventbridge

    with Cluster("Analytics & Insights", graph_attr={"bgcolor": "#e8f5e9", "style": "rounded"}):
        athena = Athena("Athena SQL")
        sagemaker = Sagemaker("SageMaker\n(ML Models)")
        curated = S3("S3 Curated\n(Scores)")
        quicksight = Quicksight("QuickSight\nDashboard")

        processed >> athena >> quicksight
        processed >> sagemaker >> curated >> quicksight
