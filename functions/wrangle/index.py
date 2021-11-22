try:
    import unzip_requirements
except ImportError:
    pass

import boto3
import json
import os
import time
import pandas as pd
import awswrangler as wr

def run_query(user_id: str, date: str):
    athena_db = os.environ.get('athena_db')
    athena_log1_table = os.environ.get('athena_log1_table')
    athena_workgroup = os.environ.get('athena_workgroup')

    query = f"SELECT * FROM {athena_log1_table} WHERE user_id = '{user_id}' AND date = '{date}';"
    df = wr.athena.read_sql_query(query, database=athena_db, workgroup=athena_workgroup)
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
