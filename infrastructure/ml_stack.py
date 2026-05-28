"""ML stack — SageMaker notebook for model development."""
from aws_cdk import (
    Stack,
    aws_sagemaker as sagemaker,
    aws_iam as iam,
)
from constructs import Construct

from infrastructure.data_lake_stack import DataLakeStack


class MLStack(Stack):
    def __init__(self, scope: Construct, id: str, data_lake: DataLakeStack, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # SageMaker execution role
        sagemaker_role = iam.Role(
            self, "SageMakerRole",
            assumed_by=iam.ServicePrincipal("sagemaker.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSageMakerFullAccess"),
            ],
        )
        data_lake.raw_bucket.grant_read(sagemaker_role)
        data_lake.processed_bucket.grant_read(sagemaker_role)
        data_lake.curated_bucket.grant_read_write(sagemaker_role)

        # Notebook instance for development (deploys in Stopped state to avoid cost)
        self.notebook = sagemaker.CfnNotebookInstance(
            self, "WellnessNotebook",
            notebook_instance_name="health-pipeline-notebook",
            instance_type="ml.t3.medium",
            role_arn=sagemaker_role.role_arn,
            volume_size_in_gb=20,
        )
        # Note: Start manually via console when ready for Phase 3
