import base64
from modules import script_callbacks, sd_models, shared
from modules.shared import opts, cmd_opts
import gradio as gr
import time
import requests
import os
import stat
from typing import List, Tuple
from modules.extras import  run_pnginfo
from PIL import Image
import os
import time

  
tab_title = 'Port resources'
tab_elem_id = tab_title + "_interface"
Assets = ['Models', 'Hypernetworks', 'Embeddings']

base_url = "http://127.0.0.1:7860"
hypernetworks_url = '/sdapi/v1/hypernetworks'
models_url = '/sdapi/v1/sd-models'
upscalers_url = '/sdapi/v1/upscalers'

resources_url = [hypernetworks_url, models_url, upscalers_url]

hyper_net_dir = cmd_opts.hypernetwork_dir or './models/hypernetworks'
embedding_dir = cmd_opts.embeddings_dir or './embeddings'
model_dir = cmd_opts.ckpt_dir or './models/Stable-diffusion'

def makeRequest(path):
    req_url = base_url + path
    r = requests.get(req_url)
    response = r.json()
    return response

import zipfile

def syncResources():
    fileNames = []
    print('--- STARTING HYPERNETWORK ---')
    fileNames.extend(sync_hypernetworks())
    print('--- FINISHED HYPERNETWORK  ---')
    print('--- STARTING MODELS ---')
    fileNames.extend(sync_models())
    print('--- FINISHED MODELS ---')
    print('--- STARTING EMBEDDED ---')
    fileNames.extend(sync_embeddings())
    print('--- FINISHED EMBEDDED ---')
    print('--- STARTING PICS ---')
    fileNames.extend(sync_pics())
    print('--- FINISHED PICS ---')

    print(fileNames)
   # Create a ZipFile object
    zip_file = zipfile.ZipFile('compressed.zip', 'w')

    # Iterate over the list of JSON files and add them to the ZipFile object
    for json_file in fileNames:
        with open(json_file, 'r') as f:
            data = json.load(f)
        zip_file.writestr(json_file, json.dumps(data))

    # Close the ZipFile object
    zip_file.close() 

def on_ui_tabs():
    with gr.Blocks(analytics_enabled=False) as auxiliary_interface:
        with gr.Row().style(equal_height=False):
            with gr.Column(variant='panel'):
                gr.HTML(value="sync resources")
                sync_button = gr.Button("SYNC")
                sync_button.click(syncResources)

    return [(auxiliary_interface, tab_title, tab_elem_id)]

script_callbacks.on_ui_tabs(on_ui_tabs)

# --------------------- READ LOCAL ---------------------

image_ext_list = [".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"]
def traverse_all_files(curr_path, image_list) -> List[Tuple[str, os.stat_result]]:
    f_list = [(os.path.join(curr_path, entry.name), entry.stat()) for entry in os.scandir(curr_path)]
    for f_info in f_list:
        fname, fstat = f_info
        if os.path.splitext(fname)[1] in image_ext_list:
            image_list.append(f_info)
        elif stat.S_ISDIR(fstat.st_mode):
            image_list = traverse_all_files(fname, image_list)
    return image_list


def get_all_images(dir_name, sort_by, keyword):
    fileinfos = traverse_all_files(dir_name, [])
    keyword = keyword.strip(" ")
    if len(keyword) != 0:
        fileinfos = [x for x in fileinfos if keyword.lower() in x[0].lower()]
    if sort_by == "date":
        fileinfos = sorted(fileinfos, key=lambda x: -x[1].st_mtime)
    elif sort_by == "path name":
        fileinfos = sorted(fileinfos)

    filenames = [finfo[0] for finfo in fileinfos]
    return filenames

import hashlib

# https://www.programiz.com/python-programming/examples/hash-file
def hash_file(filename):
   """"This function returns the SHA-1 hash
   of the file passed into it"""

   # make a hash object
   h = hashlib.sha1()

   # open file for reading in binary mode
   with open(filename,'rb') as file:

       # loop till the end of the file
       chunk = 0
       while chunk != b'':
           # read only 1024 bytes at a time
           chunk = file.read(1024)
           h.update(chunk)

   # return the hex representation of digest
   return h.hexdigest()

# file is filepath
def show_image_info(file):
    if type(file) == list and len(file) >= 1:
        file = file[0]

    openImage = Image.open(file)
    f = run_pnginfo(openImage)

    return run_pnginfo(Image.open(file))[1]

def encode_image(file):
    with open(file, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        
    return encoded_string


def encode_sample(sample : str):
    for encoding in ('ascii', 'utf8', 'utf16'):
        filename = f'{encoding}.json'
        encoded_sample = sample.encode(encoding=encoding, errors='replace')
        with open(filename, mode='wb') as f:
            f.write(encoded_sample)
            assert len(encoded_sample) == f.tell()
            print(f'{encoding}: {f.tell()} bytes')

import json

def sync_pics():
    start = time.time()
    all_images = get_all_images(opts.outdir_txt2img_samples, "","")
    count = 0 
    content = []
    failed = []
    for i, img in enumerate(all_images):
        img_abs_path = os.path.abspath(img)
        img_info = show_image_info(img)
        fileHash = hash_file(img)
        fileStats = os.stat(img)
        encoded_image = encode_image(img)

        try:
            payload = {
                "infotext": img_info,
                "localImgInfo": {
                    "absFilePath": img_abs_path,
                    "stats":  {
                        "ctime": fileStats.st_ctime,
                        "size": fileStats.st_size,
                    },
                },
                "syncSource": "local",
                "fileHash": fileHash,
                "type": "Txt2Img",
                "imgData": str(encoded_image)
            }

            content.append(payload)
            break

        except Exception as e:
            print(e)
            failed.append((img, i))
            if len(failed) >= 50:
                print("EARLY STOPPAGE")
                break
        count += 1

    fileOutName = 'pics.json'
    with open(fileOutName, 'w') as outfile:
        json_data = json.dumps(content)
        outfile.write(json_data)

    end = time.time()

    print('FINISHING STATS' + 
        '\n total: '+ str(len(all_images)) + 
        '\n failed: '+ str(len(failed)) + 
        '\n success: '+ str(len(all_images) - len(failed)) + 
        '\n time taken: '+ str(end - start) 
    )

    return fileOutName
    

def generic_sync(dir_path, file_ext, resource_name, get_hash_func):
    # png, txt is info, ignore for now
    # .pt is hypernetwork
    start = time.time()

    filelist = []
    for root, _, files in os.walk(dir_path):
        for file in files:
            #append the file name to the list
            if file.endswith(file_ext):
                path = os.path.join(root, file)
                stat = os.stat(path)
                final = {
                    'name': file.split(file_ext)[0], # remove extension
                    'path': path,
                    'stat': {
                        'ctime': stat.st_ctime,
                        'size': stat.st_size
                    },
                    'hash': get_hash_func(path)
                }
                filelist.append(final)

    total = len(filelist)
    success_count = 0 
    fileOutName = f'{resource_name}.json'
    with open(fileOutName, 'w') as outfile:
        json_data = json.dumps(filelist)
        outfile.write(json_data)

    end = time.time()
    print('FINISHING STATS for ' + resource_name +
        '\n total: '+ str(total) + 
        '\n failed : '+ str(total - success_count) + 
        '\n success: '+ str(success_count) + 
        '\n time taken: '+ str(end - start) 
    )
    return fileOutName

def sync_hypernetworks():
    fileNames = []
    fileNames.append(generic_sync(hyper_net_dir, '.pt', 'hypernetwork', sd_models.model_hash))
    return fileNames
    

def sync_models():
    fileNames = []
    fileNames.append(generic_sync(model_dir, '.ckpt', 'model', sd_models.model_hash))
    fileNames.append(generic_sync(model_dir, '.safetensors', 'model', sd_models.model_hash))
    return fileNames

def sync_embeddings():
    fileNames = []
    fileNames.append(generic_sync(embedding_dir, '.pt', 'embedding', hash_file))
    fileNames.append(generic_sync(embedding_dir, '.png', 'embedding', hash_file))
    return fileNames
