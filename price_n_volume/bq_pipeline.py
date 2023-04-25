from google.cloud import bigquery
import os
import json
import pyspark
from pyspark.sql import SparkSession, types
from pyspark.conf import SparkConf
from pyspark.context import SparkContext
from pyspark.sql.functions import udf, col
from pyspark.sql import functions as F, Window
from prefect import flow, task

@task
def get_gcs_project_id():
    location = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
    if location == None:
        print('Key not found; set `GOOGLE_APPLICATION_CREDENTIALS` env variable in bash')
        return "-1"
    data = json.load(open(location))
    return data['project_id']


def setup_for_spark():

    client = bigquery.Client()

    credentials_location = "/home/param/data-engineering-zoomcamp/week_1_basics_n_setup/1_terraform_gcp/terraform/quick-ray-375906-15748deb6a49.json"

    conf = SparkConf() \
        .setMaster('local[*]') \
        .setAppName('test') \
        .set("spark.jars", "/home/param/bin/spark-bigquery-with-dependencies_2.12-0.29.0.jar") \
        .set("spark.hadoop.google.cloud.auth.service.account.enable", "true") \
        .set("spark.hadoop.google.cloud.auth.service.account.json.keyfile", credentials_location)

    sc = SparkContext(conf=conf)

    hadoop_conf = sc._jsc.hadoopConfiguration()

    hadoop_conf.set("fs.AbstractFileSystem.gs.impl",  "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFS")
    hadoop_conf.set("fs.gs.impl", "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFileSystem")
    hadoop_conf.set("fs.gs.auth.service.account.json.keyfile", credentials_location)
    hadoop_conf.set("fs.gs.auth.service.account.enable", "true")

    spark = SparkSession.builder \
        .config(conf=sc.getConf()) \
        .getOrCreate()
    
    return client, spark

# need to change to remove (TBD)
# 1. Project name 
# 2: dataset name 
# 3. Table name
@flow
def create_bq_raw_table(client):
    project_id = get_gcs_project_id()
    dataset_name = 'prod_price_n_volume'
    datalake_name = 'lake_price_n_volume'
    query = (
        f'    CREATE OR REPLACE EXTERNAL TABLE `{project_id}.{dataset_name}.recent_raw_external`\n'
        '  OPTIONS (\n'
        '    format ="csv",\n'
        f'    uris = ["gs://{datalake_name}/data/price_n_volume/recent/*"]\n'
        '    );\n'
        '\n'
        f'    CREATE or REPLACE TABLE `{project_id}.{dataset_name}.recent_raw`\n'
        '    AS \n'
        f'    SELECT * FROM `{project_id}.{dataset_name}.recent_raw_external`;\n'

    )
    
    # Executes the query and fetches the results
    query_job = client.query(query)
    return query_job

    

def udf_if_outlier(val, avg, stddev):
    try:
        if ( 
            (val > (avg + stddev)) 
            
        ):
            return 1
        elif (
            (val < (avg - stddev)) 
        ):
            return -1
    except Exception as e:
        # print(f'e = {e}\n val = {val}, avg = {avg}, stddev = {stddev}')
        return -2
    return 0


def udf_if_outlier_high_only(val, avg, stddev):
    try:
        if ( val > (avg + stddev)):
            return 1
    except Exception as e:
        return 0
    return 0

@task
def window_create(df, on_column ,lst_number_of_days, both=1):
    for number_of_days in lst_number_of_days:
        w = Window.partitionBy('company').orderBy('date').rowsBetween(Window.currentRow+1, number_of_days)

        avg_column = f'avg_{on_column}_{number_of_days}'
        stddev_column = f'stddev_{on_column}_{number_of_days}'
        outlier_column = f'if_outlier_{on_column}_{number_of_days}'

        df = df.withColumn(
            avg_column, 
            F.avg(f'{on_column}').over(w))

        df = df.withColumn(
            stddev_column, 
            F.stddev(f'{on_column}').over(w))

        if both:
            udfValueToOutlier = udf(udf_if_outlier, types.IntegerType())
        else:
            udfValueToOutlier = udf(udf_if_outlier_high_only, types.IntegerType())

        # here does not work

        df = df.withColumn(
                outlier_column, 
                udfValueToOutlier(df[f'{on_column}'], df[f'{avg_column}'], df[f'{stddev_column}']))

        # df.select(\
        #      col("company"), col(outlier_column)
        # ).groupBy('company', outlier_column).count().orderBy(col("company")).show()
    return df

@flow
def create_bq_outlier_table(spark):
    df = spark.read \
      .format("bigquery") \
      .load("quick-ray-375906.price_n_volume.recent_raw")
    
    df = window_create(df, 'close_percent_change', [20])
    df = window_create(df, 'volume', [100], both=0)
    return df


@flow
def write_bq_outlier_table(spark, dataset = 'prod_price_n_volume', table = 'recent_outliers'):
    df = create_bq_outlier_table(spark)
    print(f'number of records in dataset: {df.count()}')
    print(f'Writing to {dataset} with table {table}')
    df.write \
      .format("bigquery").mode("overwrite") \
      .option("writeMethod", "direct") \
      .save(f"{dataset}.{table}")
    
@flow
def add_to_bigquery():
    client, spark = setup_for_spark()
    create_bq_raw_table(client)
    write_bq_outlier_table(spark)

if __name__=="__main__":
    add_to_bigquery()