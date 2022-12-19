import requests 
import time
import json
import zipfile

def send_info(resource_name, body):
    url = f"http://localhost:8080/api/v1/{resource_name}"
    r = requests.post(url, json=body)
    if r.status_code != 200 or r.status_code != 302:
        raise Exception("error")

def main():
    folder_name = "compressed.zip"
    with zipfile.ZipFile(folder_name, 'r') as zip_ref:
        # Iterate over all the files in directory
        zip_ref.extractall()

    for file in zip_ref.namelist():
        print(file)
        # if file.filename.endswith('.json'):
        #     with open(file.filename, 'r') as f:
        #         data = json.load(f)
        #         # name format is {resource_name}-{extra_info}.json
        #         resource_name = file.filename.split('-')[0]
        #         iterate_send(resource_name, data)
            
def iterate_send(resource_name, resources):
    count = 0
    failed = []
    start = time.time()
    for resource in resources:
        try:
            send_info(resource_name, resource)
            count += 1
        except Exception as e:
            failed.append(resource)
            print("failed")
    
    end = time.time()
    print('FINISHING STATS' + f' {resource_name}' + 
        '\n total: '+ str(len(resources)) + 
        '\n failed: '+ str(len(failed)) + 
        '\n success: '+ count +
        '\n time taken: '+ str(end - start) 
    )
