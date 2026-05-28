"""Data Lake stack — S3 buckets for raw, processed, and curated data."""
from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_s3 as s3,
)
from constructs import Construct


class DataLakeStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.raw_bucket = s3.Bucket(
            self, "RawBucket",
            bucket_name="health-pipeline-raw",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        self.processed_bucket = s3.Bucket(
            self, "ProcessedBucket",
            bucket_name="health-pipeline-processed",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        self.curated_bucket = s3.Bucket(
            self, "CuratedBucket",
            bucket_name="health-pipeline-curated",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )
