#!/usr/bin/env python3
"""CDK app for the Wearable Health Signal Processing Pipeline."""
import os
import aws_cdk as cdk

from infrastructure.data_lake_stack import DataLakeStack
from infrastructure.ingestion_stack import IngestionStack
from infrastructure.processing_stack import ProcessingStack
from infrastructure.ml_stack import MLStack

app = cdk.App()

env = cdk.Environment(account=os.environ.get("AWS_ACCOUNT_ID", "YOUR_ACCOUNT_ID"), region="us-east-1")

data_lake = DataLakeStack(app, "HealthPipeline-DataLake", env=env)
ingestion = IngestionStack(app, "HealthPipeline-Ingestion", env=env, data_lake=data_lake)
processing = ProcessingStack(app, "HealthPipeline-Processing", env=env, data_lake=data_lake)
ml = MLStack(app, "HealthPipeline-ML", env=env, data_lake=data_lake)

app.synth()
