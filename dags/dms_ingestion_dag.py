from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.utils.dates import days_ago
from helpers.dms_helpers import create_dms_task, start_dms_task, monitor_table_progress_function
from helpers.config_helpers import load_config
from airflow.providers.amazon.aws.sensors.dms import DmsTaskBaseSensor, DmsTaskCompletedSensor

default_args = {
    'owner': 'airflow',
    'start_date': days_ago(1),
    'retries': 0,
}

dag = DAG(
    dag_id='dms_migration_dag',
    default_args=default_args,
    schedule_interval=None,
    catchup=False,
)

load_config_task = PythonOperator(
    task_id='load_config',
    python_callable=load_config,
    dag=dag,
)

create_dms_task = PythonOperator(
    task_id='create_dms_task',
    python_callable=create_dms_task,
    provide_context=True,
    op_kwargs={'config': '{{ ti.xcom_pull(task_ids="load_config") }}'},
    dag=dag,
)

start_dms_task = PythonOperator(
    task_id='start_dms_task_instance',
    python_callable=start_dms_task,
    provide_context=True,
    op_kwargs={'replication_task_arn': '{{ ti.xcom_pull(task_ids="create_dms_task") }}'},
    dag=dag,
)

await_task_start = DmsTaskBaseSensor(
    task_id='await_task_start',
    replication_task_arn='{{ ti.xcom_pull(task_ids="create_dms_task") }}',
    target_statuses=["running"],
    termination_statuses=["stopped", "deleting", "failed"],
    aws_conn_id='aws_default',
    poke_interval=10,
    dag=dag,
)

monitor_dms_task = DmsTaskCompletedSensor(
    task_id='monitor_dms_task',
    replication_task_arn='{{ ti.xcom_pull(task_ids="create_dms_task") }}',
    aws_conn_id='aws_default',
    poke_interval=10,
    dag=dag,
)

monitor_table_progress = PythonOperator(
    task_id='monitor_table_progress',
    python_callable=monitor_table_progress_function,
    provide_context=True,
    dag=dag,
)

load_config_task >> create_dms_task >> start_dms_task >> await_task_start
await_task_start >> [monitor_table_progress, monitor_dms_task]
