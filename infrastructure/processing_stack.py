"""Processing stack — Glue ETL job and Athena database/table for querying."""
from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_glue as glue,
    aws_iam as iam,
    aws_s3 as s3,
    aws_s3_assets as s3_assets,
)
from constructs import Construct
import os

from infrastructure.data_lake_stack import DataLakeStack


class ProcessingStack(Stack):
    def __init__(self, scope: Construct, id: str, data_lake: DataLakeStack, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Glue database for Athena queries
        self.database = glue.CfnDatabase(
            self, "HealthDatabase",
            catalog_id=self.account,
            database_input=glue.CfnDatabase.DatabaseInputProperty(
                name="health_pipeline_db",
                description="Wearable health signal data lake",
            ),
        )

        # Glue crawler role
        glue_role = iam.Role(
            self, "GlueRole",
            assumed_by=iam.ServicePrincipal("glue.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSGlueServiceRole"),
            ],
        )
        data_lake.raw_bucket.grant_read(glue_role)
        data_lake.processed_bucket.grant_read_write(glue_role)
        data_lake.curated_bucket.grant_read_write(glue_role)

        # Grant access to CDK assets bucket (where ETL script is stored)
        assets_bucket = s3.Bucket.from_bucket_name(
            self, "AssetsBucket",
            f"cdk-hnb659fds-assets-{self.account}-{self.region}",
        )
        assets_bucket.grant_read(glue_role)

        # Crawler to auto-discover schema from raw data
        self.crawler = glue.CfnCrawler(
            self, "RawDataCrawler",
            name="health-pipeline-raw-crawler",
            role=glue_role.role_arn,
            database_name="health_pipeline_db",
            targets=glue.CfnCrawler.TargetsProperty(
                s3_targets=[
                    glue.CfnCrawler.S3TargetProperty(path=f"s3://{data_lake.raw_bucket.bucket_name}/"),
                ],
            ),
        )

        # Upload ETL script to S3
        etl_script = s3_assets.Asset(
            self, "ETLScript",
            path=os.path.join(os.path.dirname(__file__), "..", "src", "etl", "transform.py"),
        )

        # Glue ETL job
        self.etl_job = glue.CfnJob(
            self, "TransformJob",
            name="health-pipeline-transform",
            role=glue_role.role_arn,
            command=glue.CfnJob.JobCommandProperty(
                name="glueetl",
                python_version="3",
                script_location=etl_script.s3_object_url,
            ),
            glue_version="4.0",
            number_of_workers=2,
            worker_type="G.1X",
            default_arguments={
                "--raw_bucket": data_lake.raw_bucket.bucket_name,
                "--processed_bucket": data_lake.processed_bucket.bucket_name,
                "--database": "health_pipeline_db",
            },
        )
