# Purpose 
# 1. Push Files to gcs bucket using gcs
# 2. Push recent files to BigQuery using bigquery 
# 3. Create a script that would run everyday to update data into 
#     1. BigQuery
#     2. GCS

import os
from google.cloud import storage
import json 
import glob

def get_gcs_cred_location():
    f = open('../api_key.json')
    try:
        data = json.load(f)
    except Exception as e:
        print(f'Error: json read\n {e}')
        return "-1"
    
    if "gcs_creds_location" in data.keys():
        print(f'Key found; returning key')
        return data["gcs_creds_location"]
    else:
        print('Key not found; file should be following\n\t {"gcs_creds_location" : "your_file_location"}')
        return "-1"


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

def list_files_recursive(path):
    """
    Function that receives as a parameter a directory path
    :return list_: File List and Its Absolute Paths
    """

    import os

    files = []

    # r = root, d = directories, f = files
    for r, d, f in os.walk(path):
        for file in f:
            files.append(os.path.join(r, file))
        for d_ in d:
            files += list_files_recursive(os.path.join(r, d_))
            
            

    return files


def push_from_local(path):
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
            bucket_name="prefect-dee",
            csv_name = csv_name,
            gcs_creds_location = api_key      
        )
        print(out)


if __name__=="__main__":
    api_key = get_gcs_cred_location()
    
    if api_key == "-1":
        exit(1)

    # upload_historic

    historic_path = './data/price_n_volume/historic'

    push_from_local(path = historic_path)

    recent_path = './data/price_n_volume/recent'

    push_from_local(path = recent_path)
