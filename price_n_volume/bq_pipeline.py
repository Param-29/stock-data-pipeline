from google.cloud import bigquery
import pyspark
from pyspark.sql import SparkSession, types
from pyspark.conf import SparkConf
from pyspark.context import SparkContext
from pyspark.sql.functions import udf, col
from pyspark.sql import functions as F, Window
from prefect import flow, task


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

@task
def create_bq_raw_table(client):
    query = '''
    CREATE OR REPLACE EXTERNAL TABLE `quick-ray-375906.price_n_volume.recent_raw_external`
  OPTIONS (
    format ="csv",
    uris = ['gs://prefect-dee/data/price_n_volume/recent/*']
    );

    CREATE or REPLACE TABLE `quick-ray-375906.price_n_volume.recent_raw`
    AS 
    SELECT * FROM `quick-ray-375906.price_n_volume.recent_raw_external`;
    '''

    # Executes the query and fetches the results
    query_job = client.query(query)
    return query_job

    




# In[37]:


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

@task
def create_bq_outlier_table(spark):
    df = spark.read \
      .format("bigquery") \
      .load("quick-ray-375906.price_n_volume.recent_raw")
    
    df = window_create(df, 'close_percent_change', [20])
    df = window_create(df, 'volume', [100], both=0)
    return df


@task
def write_bq_outlier_table(spark, dataset = 'prod_price_n_volume', table = 'recent_outliers'):
    df = create_bq_outlier_table(spark)
    print(f'number of records in dataset: {df.count()}')
    print(f'Writing to {dataset} with table {table}')
    df.write \
      .format("bigquery") \
      .option("writeMethod", "direct") \
      .save(f"{dataset}.{table}")
    




if __name__=="__main__":
    client, spark = setup_for_spark()
    create_bq_raw_table(client)
    write_bq_outlier_table(spark)


