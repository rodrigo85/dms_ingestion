# AWS DMS Ingestion with Airflow Project 🚀

This project demonstrates how to use Apache Airflow to orchestrate AWS Database Migration Service (DMS) tasks for data ingestion. The solution leverages the power of Airflow for workflow automation and AWS DMS for seamless data migration to Amazon S3.

### Table of Contents 📚

- [Quick Start Guide 🏁](#quick-start-guide-)
    - [Requirements 📋](#requirements-)
    - [Setup & Installation 🛠️](#setup--installation)
    - [Running the Project ▶️](#running-the-project)
- [Defining Table Mappings and Migration Setup 🔧](#defining-table-mappings-and-migration-setup-)
- [Understanding the DAG Structure 📜](#understanding-the-dag-structure-)
    - [DAG Graph Representation](#dag-graph-representation)
    - [Managing DMS Tasks 📊](#managing-dms-tasks-)
- [Validation and Test Evidence 🧪](#validation-and-test-evidence-)

## Quick Start Guide 🏁

### Requirements 📋

This project runs within Docker containers and requires the following:

| Requirement                               | Installation Command                    |
| ----------------------------------------- | ---------------------------------------- |
| [Docker](https://www.docker.com/)         | [Install Docker Desktop](https://docs.docker.com/desktop/install/windows-install/) |
| [Docker Compose](https://docs.docker.com/compose/) | [Install Docker Compose](https://docs.docker.com/compose/install/) |

Ensure you have Docker and Docker Compose installed on your machine before proceeding.

### Setup & Installation 🛠️

1. **Clone the repository to your local machine:**

    ```bash
    git clone https://github.com/rodrigo85/dms_ingestion.git
    cd aws-dms-airflow
    ```

2. **Create AWS DMS Replication Instance and Endpoints:**
    - Before proceeding with the setup, ensure that you have created a replication instance and defined the source and target endpoints in AWS DMS. These components are necessary for the data migration process.
    - Navigate to the following paths in the AWS Management Console to set up these components:
        - **Replication Instance**:  
          Go to **AWS > DMS > Replication instances**. Here, you will create a new replication instance, which will manage the data migration tasks. Make a note of the ARN provided after creating the instance.
        - **Endpoints**:  
          Go to **AWS > DMS > Endpoints**. Here, you will create:
            - A **Source Endpoint** that points to your source database (e.g., PostgreSQL).
            - A **Target Endpoint** that points to your destination (e.g., S3 bucket).  
          Make a note of the ARNs provided for both the source and target endpoints.
        - **Database Migration Tasks**:  
          Go to **AWS > DMS > Database migration tasks**. This section is where you can monitor the migration tasks created by Airflow. Once Airflow triggers a task, it will appear here, allowing you to track its progress and status.

3. **Setup IAM User with Required Permissions:**
    - Create or use an existing IAM user with the necessary permissions to manage DMS tasks. The IAM user should have the following policy attached to allow starting, stopping, creating, and describing DMS tasks:

    ```json
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "VisualEditor0",
                "Effect": "Allow",
                "Action": [
                    "dms:StartReplicationTask",
                    "dms:StopReplicationTask",
                    "dms:CreateReplicationTask"
                ],
                "Resource": [
                    "arn:aws:dms:*:343617587099:task:*",
                    "arn:aws:dms:*:343617587099:rep:*",
                    "arn:aws:dms:*:343617587099:endpoint:*"
                ]
            },
            {
                "Sid": "VisualEditor1",
                "Effect": "Allow",
                "Action": "dms:DescribeReplicationTasks",
                "Resource": "*"
            }
        ]
    }
    ```

    - Ensure this policy is attached to the IAM user that will be used for DMS operations. Replace `343617587099` with your AWS account ID.


4. **Define environment variables:**
    - Create a `.env` file in the project root directory with the necessary configurations, including the ARNs for the replication instance and endpoints. Refer to the provided `.env.example` for guidance.

5. **Build and start the Docker containers:**
   
    ```bash
    docker-compose up --build -d
    ```

    The following image demonstrates the expected outcome of having all Docker containers successfully running for the project setup:

    <img src="https://github.com/rodrigo85/dms_ingestion/blob/main/images/airflow/containers.jpg" height="250" alt="Container Status" title="Container Status">

6. **Expose Local PostgreSQL to AWS DMS:**

    To allow AWS DMS to access your local PostgreSQL database, use Serveo to expose port 5432. This step is necessary because the database is running locally without a fixed IP address, which AWS DMS requires for connectivity.

    Run the following command in your terminal to expose your local PostgreSQL:

    ```bash
    ssh -R 15432:localhost:5432 serveo.net
    ```

    This command creates a public URL that AWS DMS can use to connect to your local PostgreSQL instance.

### Running the Project ▶️

Once the containers are up and running, access the Airflow web UI at `http://localhost:8080`. Use the default credentials provided in the `.env` file to log in. Additionally, port `5432` will be exposed for accessing the PostgreSQL database.

You must create a connection in Airflow by navigating to **Admin > Connections** and using your AWS Access Key ID and Secret Access Key.

<img src="https://github.com/rodrigo85/dms_ingestion/blob/main/images/airflow/aws_default_conn.jpg" height="250" alt="AWS Connection Setup" title="AWS Connection Setup">

### **Defining Table Mappings and Migration Setup 🔧**

The configuration for AWS Database Migration Service (DMS) is defined in the [`dms_config.json`](https://github.com/rodrigo85/dms_ingestion/blob/main/config/dms_config.json) file. This file includes essential parameters that guide the data migration tasks. Below is a breakdown of the key parameters:

https://github.com/rodrigo85/dms_ingestion/blob/c46d79da5f165f6ef8e665e62f57559e6b68761b/config/dms_config.json#L1-L12

1. **`dms_task_name`**: Specifies the unique name of the DMS task. This identifier is crucial for managing and tracking the migration task within AWS DMS.    

2. **`s3_bucket_name`**: Defines the name of the S3 bucket where the migrated data will be stored. This bucket acts as the destination for data extracted from the source database.   

3. **`table_mappings`**: Lists the schema and table names to be included in the migration. Each entry specifies a `schema_name` and `table_name` for precise data selection from the source.   

4. **`migration_type`**: Specifies the type of migration, such as `"full-load"`, to indicate that a complete data load from the source to the target will be performed.   

For the complete configuration, please refer to the [`dms_config.json` file](https://github.com/rodrigo85/dms_ingestion/blob/main/config/dms_config.json) in the repository.

## <a name="understanding-the-dag-structure">Understanding the DAG Structure 📜</a>

### DAG Graph Representation

<img src="https://github.com/rodrigo85/dms_ingestion/blob/main/images/airflow/airflow_graph.jpg" height="400" alt="DAG Graph" title="DAG Graph">

*Figure: The DAG graph shows how tasks are orchestrated to manage AWS DMS operations effectively.*

### <a name="managing-dms-tasks">Managing DMS Tasks 📊</a>

1. **Load Configuration (`load_config`)**: 
   - This task is responsible for loading the necessary configuration details from a predefined JSON file. It ensures that all subsequent tasks have access to the correct settings, such as source and target endpoints, table mappings, and replication instance ARNs.
   
2. **Create DMS Task (`create_dms_task`)**: 
   - Using the configuration details loaded in the previous step, this task sets up a new DMS replication task. It constructs the necessary table mappings and initiates the task creation process using the AWS DMS API. The task's ARN is generated and passed to subsequent tasks for further processing.

3. **Start DMS Task Instance (`start_dms_task_instance`)**: 
   - This task starts the DMS replication task that was created in the previous step. By invoking the DMS API, it begins the actual data migration process, replicating data from the source to the target endpoint as specified in the configuration.

4. **Await Task Start (`await_task_start`)**: 
   - A sensor task that checks the status of the DMS replication task, ensuring it transitions to a 'running' state. It monitors the task's state and proceeds only when the task is confirmed to be active. This ensures that the task is correctly initiated before monitoring its progress.

5. **Monitor DMS Task (`monitor_dms_task`)**: 
   - This task continuously monitors the replication task's status, checking for completion or failure.

6. **Monitor Table Progress (`monitor_table_progress`)**: 
   - A custom Python task that monitors the progress of individual tables within the replication task. It provides more granular insights, such as the number of tables loaded, loading, queued, or errored. This task is crucial for understanding the detailed status of the data migration process.

### <a name="validation-and-test-evidence">Validation and Test Evidence 🧪</a>

To ensure the DMS tasks are executed correctly and the data is ingested successfully into the S3 bucket, we provide visual evidence of the process:

1. **AWS DMS Task Overview**:
   - The image below shows the AWS DMS console displaying the migration task status. It includes table statistics such as the table name, elapsed load time, and the total number of rows uploaded, indicating that the data migration task is successfully underway.

    <img src="https://github.com/rodrigo85/dms_ingestion/blob/main/images/aws/migration_task.jpg" height="250" alt="AWS DMS Task Stats" title="AWS DMS Task Stats">

2. **S3 Bucket Structure**:
   - This image illustrates the structure of the S3 bucket after successful ingestion. Each folder represents a table that was migrated from the source database. This organization helps in verifying that each table has been correctly ingested into its corresponding directory in S3.

    <img src="https://github.com/rodrigo85/dms_ingestion/blob/main/images/aws/buckets.jpg" height="250" alt="S3 Bucket Structure" title="S3 Bucket Structure">

These images serve as evidence that the data migration process is functioning as expected, demonstrating successful ingestion and proper organization of data into S3.

#### Like the project? ⭐

Consider giving the repository a star!
