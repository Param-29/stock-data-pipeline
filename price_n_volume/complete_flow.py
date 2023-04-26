from bq_pipeline import *
from push_to_gcs import * 
from prefect import flow

@flow
def complete_flow_run():
    push_to_gcs_flow()
    add_to_bigquery()

if __name__=="__main__":
    complete_flow_run()