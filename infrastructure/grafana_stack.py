# WIP - Not used in current deployment (requires SSO or SSH tunnel)
"""Grafana stack — Amazon Managed Grafana workspace with Athena + CloudWatch data sources."""
from aws_cdk import (
    Stack,
    aws_grafana as grafana,
    aws_iam as iam,
)
from constructs import Construct

from infrastructure.data_lake_stack import DataLakeStack


class GrafanaStack(Stack):
    def __init__(self, scope: Construct, id: str, data_lake: DataLakeStack, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Grafana workspace role
        grafana_role = iam.Role(
            self, "GrafanaRole",
            assumed_by=iam.ServicePrincipal("grafana.amazonaws.com"),
            inline_policies={
                "AthenaAccess": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=[
                                "athena:GetQueryExecution",
                                "athena:GetQueryResults",
                                "athena:StartQueryExecution",
                                "athena:StopQueryExecution",
                                "athena:ListDatabases",
                                "athena:ListTableMetadata",
                                "athena:GetDatabase",
                                "athena:GetTableMetadata",
                            ],
                            resources=["*"],
                        ),
                        iam.PolicyStatement(
                            actions=["glue:GetDatabase", "glue:GetDatabases", "glue:GetTable", "glue:GetTables", "glue:GetPartitions"],
                            resources=["*"],
                        ),
                    ]
                ),
                "S3Access": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=["s3:GetObject", "s3:ListBucket", "s3:PutObject"],
                            resources=[
                                data_lake.processed_bucket.bucket_arn,
                                f"{data_lake.processed_bucket.bucket_arn}/*",
                                data_lake.curated_bucket.bucket_arn,
                                f"{data_lake.curated_bucket.bucket_arn}/*",
                                # Athena query results
                                f"arn:aws:s3:::health-pipeline-processed-{self.account}",
                                f"arn:aws:s3:::health-pipeline-processed-{self.account}/*",
                            ],
                        ),
                    ]
                ),
                "CloudWatchAccess": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=[
                                "cloudwatch:GetMetricData",
                                "cloudwatch:ListMetrics",
                                "cloudwatch:GetMetricStatistics",
                                "cloudwatch:DescribeAlarms",
                            ],
                            resources=["*"],
                        ),
                    ]
                ),
            },
        )

        # Managed Grafana workspace
        self.workspace = grafana.CfnWorkspace(
            self, "HealthDashboard",
            name="health-pipeline-dashboard",
            account_access_type="CURRENT_ACCOUNT",
            authentication_providers=["AWS_SSO"],
            permission_type="SERVICE_MANAGED",
            role_arn=grafana_role.role_arn,
            data_sources=["ATHENA", "CLOUDWATCH"],
            description="Wearable Health Pipeline — Real-time and historical wellness dashboard",
        )
