# Geospatial Precipitation Job

This README provides instructions for setting up and running a Docker Compose environment to run the Geospatial Precipitation Job. This includes PySpark, Hive, Airflow, and Jupyter Notebooks. Follow the steps below to get started.


## Work in Progress
1. Airflow task needs to run the pyspark script located in the spark container. The connection between containers is not identifying the script.
2. Integrate Spark SQL (Hive) to Jupyter Notebook so users can use SQL queries directly without using Spark wrappers.
3. Due limited compute resources the script is hardcoded only to read one day.

## Prerequisites

- **Docker**: Ensure Docker is installed on your system. You can download Docker from [the official Docker website](https://www.docker.com/get-started).

## Setup Instructions

1. **Build Docker Images**

   Navigate to the project directory where the `Dockerfile` and `docker-compose.yml` are located and build the Docker images using the following command:

   ```bash
   docker-compose build
    ```

2. **Start the Docker Compose Environment**

    Start the Docker Compose services using:

    ```bash
    docker-compose up -d
    ```
    This command will start all the containers in the background.

3. **Verify the Setup**

    Airflow Web UI: Access the Airflow web interface at http://localhost:8081/. You can monitor and manually trigger DAGs here.

    Jupyter Notebooks: Access Jupyter Notebooks at http://localhost:8888/. You can run the queries from here.

## Running the PySpark Script

1. **Access Airflow UI**
    Navigate to http://localhost:8081/ and log in to the Airflow UI.

2. **Trigger the DAG Manually**

    Find the DAG named run_pyspark_job in the Airflow dashboard.
    Trigger the DAG manually by clicking on the "Trigger Dag" button.
    This will execute the PySpark script located at /opt/spark/scripts/main.py.


## Execute job from Notebooks

1. **Access Jupyter Notebook**

    Go to http://localhost:8888/.

2. **Run main notebook**

    Go to main_notebook and run it. You can change the path as your wish if you want to try additional dates.

## Execute Queries from Notebooks

1. **Access Jupyter Notebook**

    Go to http://localhost:8888/.

2. **Run queries notebook**

    Go to queries notebook. There are 3 choices of queries that you can run. Select the one that you desire and paste it in
    ```
        selected_query = query_h3_index_summary  # Change this to run a different query

    ```