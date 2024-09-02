from pyspark.sql import SparkSession
from pyspark.sql.functions import col, udf
from pyspark.sql.functions import to_date
from pyspark.sql.types import StringType
import h3
import pandas as pd
import numpy as np
import xarray as xr
import gcsfs


# Initialize Spark session
spark = SparkSession.builder \
    .appName("PrecipitationApp") \
    .config("spark.master", "local[*]") \
    .config("spark.sql.warehouse.dir", "/home/jovyan/work/spark-warehouse") \
    .config("spark.sql.parquet.compression.codec", "snappy") \
    .config("spark.memory.fraction", "0.6") \
    .getOrCreate()

#    .config("spark.driver.memory", "1g") \
#    .config("spark.executor.memory", "1g") \
#    .config("spark.executor.cores", "2") \

# Path to the files in GCS
file_path_pattern = "gs://gcp-public-data-arco-era5/raw/date-variable-single_level/2022/12/01/total_precipitation/surface.nc"

# Use gcsfs to open the files directly from GCS
fs = gcsfs.GCSFileSystem()
file_paths = fs.glob(file_path_pattern)

# Initialize empty list to store DataFrames
data_frames = []

for file_path in file_paths:
    print(f"- Reading {file_path}...")
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
    # Count the number of rows
    print(f"Number of rows: {df.shape[0]}")
    
    print("- Creating Spark DataFrame...")
    df_spark = spark.createDataFrame(df)
    df_spark = df_spark.withColumn('date', to_date(col('timestamp')))

    # Define UDF to convert lat/lon to H3 index
    def lat_lon_to_h3(lat, lon, resolution):
        return h3.geo_to_h3(lat, lon, resolution)

    h3_udf = udf(lambda lat, lon: lat_lon_to_h3(lat, lon, resolution=3), StringType())

    # Add H3 index to Spark DataFrame
    df_h3 = df_spark.withColumn('h3_index', h3_udf(col('latitude'), col('longitude')))

    # Count the number of rows
    print(f"Number of rows after adding index: {df_h3.count()}")

    # Save the result to a parquet file
    print("- Writing output...")
    df_h3.partitionBy("date", "h3_index").write.parquet("/home/jovyan/work/data/precipitation")