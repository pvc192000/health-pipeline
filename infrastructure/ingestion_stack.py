"""Ingestion stack — Kinesis stream for real-time wearable data and Firehose to S3."""
from aws_cdk import (
    Stack,
    Duration,
    aws_kinesis as kinesis,
    aws_kinesisfirehose as firehose,
    aws_iam as iam,
)
from constructs import Construct

from infrastructure.data_lake_stack import DataLakeStack


class IngestionStack(Stack):
    def __init__(self, scope: Construct, id: str, data_lake: DataLakeStack, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.stream = kinesis.Stream(
            self, "WearableDataStream",
            stream_name="health-pipeline-wearable-stream",
            shard_count=1,
            retention_period=Duration.hours(24),
        )

        # Firehose delivery role
        firehose_role = iam.Role(
            self, "FirehoseRole",
            assumed_by=iam.ServicePrincipal("firehose.amazonaws.com"),
            inline_policies={
                "KinesisAccess": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=["kinesis:DescribeStream", "kinesis:GetShardIterator",
                                     "kinesis:GetRecords", "kinesis:ListShards"],
                            resources=[self.stream.stream_arn],
                        ),
                    ]
                ),
            },
        )
        data_lake.raw_bucket.grant_read_write(firehose_role)

        # Firehose delivers from Kinesis stream to S3 raw bucket
        self.delivery_stream = firehose.CfnDeliveryStream(
            self, "DeliveryStream",
            delivery_stream_name="health-pipeline-delivery",
            delivery_stream_type="KinesisStreamAsSource",
            kinesis_stream_source_configuration=firehose.CfnDeliveryStream.KinesisStreamSourceConfigurationProperty(
                kinesis_stream_arn=self.stream.stream_arn,
                role_arn=firehose_role.role_arn,
            ),
            s3_destination_configuration=firehose.CfnDeliveryStream.S3DestinationConfigurationProperty(
                bucket_arn=data_lake.raw_bucket.bucket_arn,
                role_arn=firehose_role.role_arn,
                prefix="kinesis/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/",
                error_output_prefix="errors/",
                buffering_hints=firehose.CfnDeliveryStream.BufferingHintsProperty(
                    interval_in_seconds=60,
                    size_in_m_bs=5,
                ),
            ),
        )
