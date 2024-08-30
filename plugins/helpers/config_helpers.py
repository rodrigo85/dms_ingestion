import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def load_config():
    """
    Loads the DMS configuration from a JSON file and replaces the ARNs with 
    those loaded from environment variables.

    This function reads the configuration from the specified JSON file, 
    replaces placeholder ARNs with actual values loaded from the environment 
    variables, and prints the updated configuration.

    Returns:
        dict: The updated DMS configuration dictionary with ARNs replaced.
    """
    
    with open('/opt/airflow/config/dms_config.json', 'r') as f:
        config = json.load(f)    
    
    config['source_endpoint_arn'] = os.getenv('SOURCE_ENDPOINT_ARN')
    config['target_endpoint_arn'] = os.getenv('TARGET_ENDPOINT_ARN')
    config['replication_instance_arn'] = os.getenv('REPLICATION_INSTANCE_ARN')
    
    return config

def get_s3_path(config, path_type):
    """
    Constructs the S3 path for raw, processed, or temp data.
    
    Args:
        config (dict): Configuration dictionary.
        path_type (str): Type of path ('raw_data_path', 'processed_data_path', 'temp_data_path').

    Returns:
        str: Full S3 path.
    """
    s3_bucket_name = config['s3_bucket_name']
    path = config[path_type]
    return f"s3://{s3_bucket_name}{path}"
