"""Lambda handler: triggers SageMaker Processing Job for wellness scoring."""
import boto3
import json
from datetime import datetime

def handler(event, context):
    sm = boto3.client("sagemaker", region_name="us-east-1")
    
    job_name = f"health-scoring-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    response = sm.create_processing_job(
        ProcessingJobName=job_name,
        RoleArn="os.environ.get("SAGEMAKER_ROLE_ARN", "YOUR_SAGEMAKER_ROLE_ARN")",
        AppSpecification={
            "ImageUri": "683313688378.dkr.ecr.us-east-1.amazonaws.com/sagemaker-scikit-learn:1.2-1-cpu-py3",
            "ContainerEntrypoint": ["python3", "/opt/ml/processing/input/train_and_score.py"],
        },
        ProcessingInputs=[{
            "InputName": "code",
            "S3Input": {
                "S3Uri": "s3://health-pipeline-raw/scripts/train_and_score.py",
                "LocalPath": "/opt/ml/processing/input",
                "S3DataType": "S3Prefix",
                "S3InputMode": "File",
            }
        }],
        ProcessingResources={
            "ClusterConfig": {
                "InstanceCount": 1,
                "InstanceType": "ml.t3.medium",
                "VolumeSizeInGB": 10,
            }
        },
        Environment={
            "PROCESSED_BUCKET": "health-pipeline-processed",
            "CURATED_BUCKET": "health-pipeline-curated",
            "AWS_DEFAULT_REGION": "us-east-1",
        },
        StoppingCondition={"MaxRuntimeInSeconds": 600},
    )
    
    print(f"Started SageMaker Processing Job: {job_name}")
    return {"statusCode": 200, "body": json.dumps({"jobName": job_name})}
