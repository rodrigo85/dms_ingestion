import json
from airflow.providers.amazon.aws.operators.dms import DmsCreateTaskOperator, DmsStartTaskOperator, DmsDescribeTasksOperator
from airflow.models.taskinstance import TaskInstance
import time
import uuid

def create_dms_task(**kwargs):
    """
    Creates a DMS replication task using configuration details provided in the kwargs.

    This function constructs the table mappings based on the configuration and then
    creates a DMS task using the DmsCreateTaskOperator. The task is configured with
    the specified source and target endpoint ARNs, migration type, table mappings,
    and replication instance ARN.

    Args:
        **kwargs: Keyword arguments that include:
            - config (str): JSON string containing DMS configuration details.
            - dag (DAG): The Airflow DAG object.

    Returns:
        dict: The result of the DMS task execution.
    """
    
    config_str = kwargs.get('config').replace("'", '"')
    config = json.loads(config_str)    
    
    table_mappings = {
        "rules": [
            {
                "rule-type": "selection",
                "rule-id": str(i + 1),
                "rule-name": str(i + 1),
                "object-locator": {
                    "schema-name": table['schema_name'],
                    "table-name": table['table_name']
                },
                "rule-action": "include"
            }
            for i, table in enumerate(config['table_mappings'])
        ]
    }

    dms_task = DmsCreateTaskOperator(
        task_id='create_dms_task_tables',
        replication_task_id=config['dms_task_name'],
        source_endpoint_arn=config['source_endpoint_arn'],
        target_endpoint_arn=config['target_endpoint_arn'],
        migration_type=config['migration_type'],
        table_mappings=table_mappings,
        replication_instance_arn=config['replication_instance_arn'],
        aws_conn_id='aws_default',
        dag=kwargs['dag'],
    )

    return dms_task.execute(context=kwargs)

def start_dms_task(**kwargs):
    """
    Starts an existing DMS replication task.

    This function uses the DmsStartTaskOperator to start a DMS task
    with the specified replication task ARN.

    Args:
        **kwargs: Keyword arguments that include:
            - replication_task_arn (str): ARN of the replication task to start.
            - dag (DAG): The Airflow DAG object.

    Returns:
        dict: The result of the DMS task start operation.
    """
    
    replication_task_arn = kwargs['replication_task_arn']

    start_task = DmsStartTaskOperator(
        task_id='start_dms_task',
        replication_task_arn=replication_task_arn,
        start_replication_task_type='start-replication',
        aws_conn_id='aws_default',
        dag=kwargs['dag'],
    )

    return start_task.execute(context=kwargs)

def monitor_table_progress_function(**kwargs):
    """
    Monitors the progress of a DMS replication task.

    This function repeatedly checks the status of a DMS task and logs its progress.
    It uses the DmsDescribeTasksOperator to fetch task details and monitor the replication
    task's statistics, such as load progress, elapsed time, and table status.

    Args:
        **kwargs: Keyword arguments that include:
            - dag_run (DAGRun): The current DAG run object.
            - ti (TaskInstance): Task instance used for XCom and logging.
            - dag (DAG): The Airflow DAG object.

    Returns:
        None: The function logs the progress and terminates when the task completes.
    """
    
    dag_run = kwargs['dag_run']
    monitor_task_instance = TaskInstance(
        task=kwargs['dag'].get_task('monitor_dms_task'),
        execution_date=dag_run.execution_date
    )

    while True:
        monitor_task_instance.refresh_from_db()
        monitor_dms_status = monitor_task_instance.state
        
        unique_task_id = f"describe_task_status_instance_{str(uuid.uuid4())[:8]}"
        
        describe_task_status = DmsDescribeTasksOperator(
            task_id=unique_task_id,
            describe_tasks_kwargs={
                "Filters": [
                    {
                        "Name": "replication-task-arn",
                        "Values": [kwargs['ti'].xcom_pull(task_ids="create_dms_task")],
                    }
                ]
            },
            aws_conn_id='aws_default',
            dag=kwargs['dag'],
        )
        
        response = describe_task_status.execute(context=kwargs)
        
        if response and len(response) > 1:
            task_details = response[1]
            if task_details and 'ReplicationTaskStats' in task_details[0]:
                replication_task_stats = task_details[0]['ReplicationTaskStats']
                
                stats_output = (
                    f"ReplicationTaskStats:\n"
                    f"  FullLoadProgressPercent: {replication_task_stats['FullLoadProgressPercent']}\n"
                    f"  ElapsedTimeMillis: {replication_task_stats['ElapsedTimeMillis']}\n"
                    f"  TablesLoaded: {replication_task_stats['TablesLoaded']}\n"
                    f"  TablesLoading: {replication_task_stats['TablesLoading']}\n"
                    f"  TablesQueued: {replication_task_stats['TablesQueued']}\n"
                    f"  TablesErrored: {replication_task_stats['TablesErrored']}\n"
                )
                
                print(stats_output)
                kwargs['ti'].log.info(stats_output)
        
        if monitor_dms_status in ['success', 'failed']:
            if monitor_dms_status == 'failed':
                kwargs['ti'].log.error("DMS Task has failed. Stopping progress monitoring.")
            break
        
        time.sleep(30)
