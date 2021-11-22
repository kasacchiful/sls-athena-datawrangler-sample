import pandas as pd
from pyarrow import Table, schema, parquet as pq
import pyarrow
import boto3

import datetime
import random
import string
import os
import re
import sys
import shutil

# params
output_path = os.path.join(os.path.dirname('__file__'), 'output_parquet/')
user_count = 5
post_count = 10  # by user
start_date = datetime.datetime.strptime('2021/11/01', '%Y/%m/%d')

def parquet_column_types():
    column_types = {
        'user_id': pyarrow.string(),
        'date': pyarrow.string(),
        'id': pyarrow.string(),
        'title': pyarrow.string(),
        'body': pyarrow.string()
    }
    return column_types

def exists_bucket(s3cli, bucket_name):
    try:
        response = s3cli.list_buckets()
        for bucket in response.buckets:
            if bucket.name == bucket_name:
                return True
        return False
    except Exception as e:
        print(f'Error listing buckets: {e}')
        return False

def generate_user_id_list():
    tmp = [ str(i) for i in range(1, user_count+1) ]
    user_ids = ['0'] * len(tmp) * post_count

    for n in range(len(tmp)):
        user_ids[n*post_count] = tmp[n]

    for idx, n in enumerate(user_ids):
        if (idx != 0) and (n == '0'):
            user_ids[idx] = user_ids[idx - 1]
    return user_ids

def generate_date_list():
    # date
    datelist = []
    for i in range(post_count):
        datelist.append((start_date + datetime.timedelta(days=i)).strftime('%Y/%m/%d'))
    datelist *= user_count
    return datelist

def generate_id_list():
    # id
    idlist = [ str(i) for i in range(1, post_count*user_count+1) ]
    return idlist

def generate_title_list(n=15):
    # title
    title_list = [ randomname(n) for i in range(post_count*user_count) ]
    return title_list

def generate_body_list(n=50):
    # body
    body_list = [ randomname(n) for i in range(post_count*user_count) ]
    body_list

def randomname(n):
   return ''.join(random.choices(string.ascii_letters + string.digits, k=n))

# main
if __name__ == '__main__':
    ## コマンド引数
    args = sys.argv
    if len(args) != 2:
        raise('Argument Error.')
    else:
        bucket_name = args[1]

    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucket_name)

    ## バケット存在確認
    ## (バケット内のオブジェクトを取得してエラーにならなければOK)
    try:
        objlist = list(bucket.objects.filter())
    except Exception as e:
        print(f'Backet is not found {bucket_name}: {e}')
        raise

    ## データフレーム作成
    df = pd.DataFrame({
        'user_id': generate_user_id_list(),
        'date': generate_date_list(),
        'id': generate_id_list(),
        'title': generate_title_list(),
        'body': generate_body_list(),
    })

    ## Parquetファイル出力
    pyarrow_table = Table.from_pandas(
        df,
        schema(parquet_column_types()),
        preserve_index=False
    )
    df.to_parquet(output_path, compression="gzip", partition_cols=['user_id', 'date'])

    ## S3アップロード
    for idx1, (path, directory, files) in enumerate(os.walk(output_path)):
        for idx2, f in enumerate(files):
            if '.parquet' in f:
                path_tmp = re.sub(r'/user_id=([0-9]+)/', r'/\1/', path)
                path_tmp = re.sub(r'/date=([0-9]+)/', r'/\1/', path_tmp)
                s3_objkey = re.sub(output_path, r'log1/', os.path.join(path_tmp, f'sample_data_{idx1}_{idx2}.parquet'))
                print(s3_objkey)
                bucket.upload_file(os.path.join(path, f), s3_objkey)

    ## Parquetファイル削除(ディレクトリ毎)
    shutil.rmtree(output_path)
