from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from datetime import datetime
from airflow.providers.docker.operators.docker import DockerOperator

# Define the default_args dictionary
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'retries': 1,
}

# Initialize the DAG
dag = DAG(
    'precipitation_h3_job',
    default_args=default_args,
    description='Precipitation job',
    schedule_interval=None,  # Manual trigger
    catchup=False,
)

# Define the BashOperator to execute the PySpark script
run_pyspark_script = DockerOperator(
    task_id='run_pyspark_script',
    image='jupyter/pyspark-notebook:latest',  # Make sure this is the correct Spark image
    #command='/spark/bin/spark-submit /opt/spark/scripts/main.py',
    #command='/usr/local/spark-3.5.0-bin-hadoop3/bin/spark-submit /home/jovyan/work/main.py',
    command = 'ls -l /home/jovyan/work',
    docker_url='unix://var/run/docker.sock',  # Ensure Docker URL is correct
    network_mode='bridge',  # Ensure this is correctly set based on your Docker network setup
    api_version='auto',
    mount_tmp_dir=False,  # Disable mounting of temporary directories
    dag=dag,
)

# Set the task order
run_pyspark_script
