"""Glue ETL job: reads raw CSV from S3, transforms to Parquet, writes to processed bucket."""
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql import functions as F

args = getResolvedOptions(sys.argv, ["JOB_NAME", "raw_bucket", "processed_bucket", "database"])

sc = SparkContext()
glue_context = GlueContext(sc)
spark = glue_context.spark_session
job = Job(glue_context)
job.init(args["JOB_NAME"], args)

raw_bucket = args["raw_bucket"]
processed_bucket = args["processed_bucket"]

# Read raw CSV data (LifeSnaps daily summaries)
df = spark.read.option("header", "true").option("inferSchema", "true").csv(
    f"s3://{raw_bucket}/lifesnaps/csv_rais_anonymized/daily_fitbit_sema_df_unprocessed.csv"
)

# Drop unnamed index column and rename for clarity
df = df.drop("_c0") if "_c0" in df.columns else df

# Cast date and add partition columns
df = (
    df.withColumn("date", F.to_date(F.col("date")))
    .withColumn("year", F.year("date"))
    .withColumn("month", F.month("date"))
    .withColumn("participant_id", F.col("id").cast("string"))
)

# Cast numeric columns
numeric_cols = [
    "nightly_temperature", "nremhr", "rmssd", "spo2", "full_sleep_breathing_rate",
    "stress_score", "calories", "filteredDemographicVO2Max", "distance", "bpm",
    "resting_hr", "sleep_duration", "minutesAsleep", "minutesAwake",
    "sleep_efficiency", "sleep_deep_ratio", "sleep_wake_ratio", "sleep_light_ratio",
    "sleep_rem_ratio", "steps", "lightly_active_minutes", "moderately_active_minutes",
    "very_active_minutes", "sedentary_minutes", "daily_temperature_variation",
]
for col in numeric_cols:
    if col in df.columns:
        df = df.withColumn(col, F.col(col).cast("double"))

# Write as partitioned Parquet
df.write.mode("overwrite").partitionBy("year", "month").parquet(
    f"s3://{processed_bucket}/daily_summaries/"
)

# Also process hourly data
df_hourly = spark.read.option("header", "true").option("inferSchema", "true").csv(
    f"s3://{raw_bucket}/lifesnaps/csv_rais_anonymized/hourly_fitbit_sema_df_unprocessed.csv"
)
df_hourly = df_hourly.drop("_c0") if "_c0" in df_hourly.columns else df_hourly

if "date" in df_hourly.columns:
    df_hourly = (
        df_hourly.withColumn("date", F.to_date(F.col("date")))
        .withColumn("year", F.year("date"))
        .withColumn("month", F.month("date"))
    )
    df_hourly.write.mode("overwrite").partitionBy("year", "month").parquet(
        f"s3://{processed_bucket}/hourly_summaries/"
    )

job.commit()
