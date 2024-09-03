import logging
import h3
import numpy as np
import pandas as pd
import xarray as xr
import gcsfs
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, udf, to_date
from pyspark.sql.types import StringType

# Constants
FILE_PATH_PATTERN = "gs://gcp-public-data-arco-era5/raw/date-variable-single_level/2022/12/01/total_precipitation/surface.nc"
PARQUET_OUTPUT_PATH = "/home/jovyan/work/data/precipitation"
H3_RESOLUTION = 3

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_spark_session():
    """Initialize and return a Spark session."""
    return SparkSession.builder \
        .appName("PrecipitationApp") \
        .config("spark.master", "local[*]") \
        .config("spark.sql.warehouse.dir", "/home/jovyan/work/spark-warehouse") \
        .config("spark.sql.parquet.compression.codec", "snappy") \
        .config("spark.memory.fraction", "0.6") \
        .getOrCreate()

def read_data_from_gcs(file_path_pattern):
    """Read data files from GCS using gcsfs."""
    fs = gcsfs.GCSFileSystem()
    file_paths = fs.glob(file_path_pattern)
    return file_paths

def process_file(file_path, fs):
    """Process a single file and return a pandas DataFrame."""
    logger.info(f"Reading {file_path}...")
    with fs.open(file_path, 'rb') as f:
        data = xr.open_dataset(f, engine='scipy')
    
    lats = data['latitude'].values
    lons = data['longitude'].values
    precipitation = data['tp'].values
    time = data['time'].values

    lats_flat = np.repeat(lats, len(lons) * len(time))
    lons_flat = np.tile(np.repeat(lons, len(time)), len(lats))
    precipitation_flat = precipitation.flatten()
    time_flat = np.tile(time, len(lats) * len(lons))
    
    df = pd.DataFrame({
        'latitude': lats_flat,
        'longitude': lons_flat,
        'timestamp': pd.to_datetime(time_flat),
        'precipitation': precipitation_flat
    })
    
    logger.info(f"Number of rows: {df.shape[0]}")
    return df.head(10000)  # Limit to 10,000 rows

def create_spark_dataframe(df, spark):
    """Convert a pandas DataFrame to a Spark DataFrame and add a date column."""
    logger.info("- Creating Spark DataFrame...")
    df_spark = spark.createDataFrame(df)
    return df_spark.withColumn('date', to_date(col('timestamp')))

def lat_lon_to_h3(lat, lon, resolution):
    """Convert latitude and longitude to H3 index."""
    return h3.geo_to_h3(lat, lon, resolution)

def add_h3_index(df_spark):
    """Add H3 index to the Spark DataFrame."""
    h3_udf = udf(lambda lat, lon: lat_lon_to_h3(lat, lon, H3_RESOLUTION), StringType())
    return df_spark.withColumn('h3_index', h3_udf(col('latitude'), col('longitude')))

def write_to_parquet(df_h3):
    """Write the Spark DataFrame to a parquet file."""
    logger.info("- Writing output...")
    df_h3.write.mode("overwrite").partitionBy("date", "h3_index").parquet(PARQUET_OUTPUT_PATH)

def main():
    """Main function to run the ETL pipeline."""
    spark = initialize_spark_session()
    file_paths = read_data_from_gcs(FILE_PATH_PATTERN)
    fs = gcsfs.GCSFileSystem()
    
    for file_path in file_paths:
        df = process_file(file_path, fs)
        df_spark = create_spark_dataframe(df, spark)
        df_h3 = add_h3_index(df_spark)
        
        logger.info(f"Number of rows after adding index: {df_h3.count()}")
        write_to_parquet(df_h3)

if __name__ == "__main__":
    main()
