# Purpose 
# 1. Push Files to gcs bucket using gcs
# 2. Push recent files to BigQuery using bigquery 
# 3. Create a script that would run everyday to update data into 
#     1. BigQuery
#     2. GCS

# "~/data-engineering-zoomcamp/week_1_basics_n_setup/1_terraform_gcp/terraform/quick-ray-375906-15748deb6a49.json"
import os
from google.cloud import storage
import json 
import glob
from prefect import flow, task

@task
def get_gcs_cred_location():
    location = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
    if location == None:
        print('Key not found; set `GOOGLE_APPLICATION_CREDENTIALS` env variable in bash')
        return "-1"
    return location

@task
def upload_all_to_bucket(dir_file, blob_name, bucket_name, csv_name, gcs_creds_location):
    """ Upload data to a bucket"""
     
    # Explicitly use service account credentials by specifying the private key
    # file.
    path_to_file = f'{dir_file}/{csv_name}'
    storage_client = storage.Client.from_service_account_json(
        gcs_creds_location)

    #print(buckets = list(storage_client.list_buckets())

    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(f'{blob_name}/{csv_name}')
    blob.upload_from_filename(path_to_file)
    
    #returns a public url
    return blob.public_url

@task
def list_files_recursive(path):
    """
    Function that receives as a parameter a directory path
    :return list_: File List and Its Absolute Paths
    """

    files = []

    # r = root, d = directories, f = files
    for r, d, f in os.walk(path):
        for file in f:
            files.append(os.path.join(r, file))
        for d_ in d:
            files += list_files_recursive(os.path.join(r, d_))
            
            

    return files

@flow
def push_from_local(path, api_key):
    lst = list_files_recursive(path)
    print(len(lst))
    for l in lst:
        # print (l, type(l))
        csv_name = os.path.basename(l).split('/')[-1]
        
        
        dir_file = os.path.dirname(l)
        
        blob_name = '/'.join(
           str(e) for e in os.path.dirname(l).split('/')[1:]
        ) 
        
        print(f'Uploading {csv_name} from {blob_name}')
        print(f'Dir name = {dir_file}')
        
        out = upload_all_to_bucket(
            dir_file = dir_file,
            blob_name=blob_name, 
            bucket_name="lake_price_n_volume",
            csv_name = csv_name,
            gcs_creds_location = api_key      
        )
        # print(out)

@flow
def push_to_gcs_flow():
    api_key = get_gcs_cred_location()
    
    if api_key == "-1":
        exit(1)

    # upload_historic

    historic_path = './data/price_n_volume/historic'

    push_from_local(path = historic_path, api_key= api_key)

    recent_path = './data/price_n_volume/recent'

    push_from_local(path = recent_path, api_key= api_key)

if __name__=="__main__":
    push_to_gcs_flow()