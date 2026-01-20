from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'pangorin',
    'start_date': datetime(2026, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'weather_data_pipeline',
    default_args=default_args,
    description='Run existing weather pipeline every 3 days',
    # Cron expression for every 3 days
    schedule_interval='0 0 */3 * *',
    catchup=False,
) as dag:
    
    # Task 1: Extraction script
    extract_task = BashOperator(
        task_id='extract_weather_data',
        bash_command='python /opt/airflow/scripts/extract.py',
    )

    # Task 2: Transformation script
    transform_task = BashOperator(
        task_id='transform_weather_data',
        bash_command='python /opt/airflow/scripts/transform.py',
    )

    # Task 3: Load to Database script
    load_task = BashOperator(
        task_id='load_weather_data_to_db',
        bash_command='python /opt/airflow/scripts/load.py',
    )

    extract_task >> transform_task >> load_task