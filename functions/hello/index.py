try:
    import unzip_requirements
except ImportError:
    pass

import boto3
import json
import os
import time
import pandas as pd

def run_query(user_id: str, date: str):
    athena_db = os.environ.get('athena_db')
    athena_log1_table = os.environ.get('athena_log1_table')
    athena_workgroup = os.environ.get('athena_workgroup')
    athena_result_bucket = os.environ.get('athena_result_bucket')
    athena_result_prefix = 'result'
    # athena_result_location = f's3://{athena_result_bucket}/{athena_result_prefix}/'

    athena = boto3.client('athena')
    s3 = boto3.client('s3')
    query = f"SELECT * FROM {athena_log1_table} WHERE user_id = '{user_id}' AND date = '{date}';"

    ## exec
    response = athena.start_query_execution(
        QueryString=query,
        QueryExecutionContext={
            'Database': athena_db
        },
        WorkGroup=athena_workgroup
    )
    ## get query execution id
    query_execution_id = response['QueryExecutionId']
    ## get execution status
    for i in range(1, 30):
        ## get query execution
        query_exec = athena.get_query_execution(QueryExecutionId=query_execution_id)
        query_execution_status = query_exec['QueryExecution']['Status']['State']
        if query_execution_status == 'SUCCEEDED':
            break
        if query_execution_status == 'FAILED':
            raise
        else:
            time.sleep(i)
    else:
        athena.stop_query_execution(QueryExecutionId=query_execution_id)
        raise
    ## get query results
    if query_execution_status == 'SUCCEEDED':
        response = s3.get_object(
            Bucket = athena_result_bucket,
            Key = f'{athena_result_prefix}/{query_execution_id}.csv'
        )
        df = pd.read_csv(response['Body'], dtype='object')
        ## delete s3 object
        obj_list = [
            { 'Key': f'{athena_result_prefix}/{query_execution_id}.csv' },
            { 'Key': f'{athena_result_prefix}/{query_execution_id}.csv.metadata' },
        ]
        response = s3.delete_objects(
            Bucket = athena_result_bucket,
            Delete = { 'Objects': obj_list, 'Quiet': True },
        )
        return df

def handler(event, context):
    # params = event.get('queryStringParameters')
    df = run_query('4', '2021/11/02')
    print(df)

    response = {
        "statusCode": 200,
        "body": df.to_json(force_ascii=False)
    }

    return response
