from modules import script_callbacks, sd_models, shared
import gradio as gr
from pprint import pprint
from modules.hypernetworks import hypernetwork
import requests
  
tab_title = 'Port resources'
tab_elem_id = tab_title + "_interface"
Assets = ['Models', 'Hypernetworks', 'Embeddings']

def pickModelFields(checkpointInfo: sd_models.CheckpointInfo):
    return checkpointInfo[2:-1]

def parseHypernetworkName(hypernetwork: str):
    # input: Senri2-10000(e3b0c442)
    # output: ("Senri2", "10000", "e3b0c442")
    # assumes that the name is in the format of <name>-<epoch>(<hash>) '-' and <epoch> is optional
    # return a tuple of (name, epoch, hash)

    if hypernetwork == '':
        raise Exception()

    # To populate
    name = ''
    epoch = ''
    hyp_hash = ''

    # assume that hash is always given 
    hash_split = hypernetwork.split('(')
    # [:-1] to remove the last ')'
    hyp_hash = hash_split[-1][:-1]

    name = "(".join(hash_split[:-1])
    dash_split = name.split('-')
    if len(dash_split) == 1:
        epoch = ""
    else:
        epoch = dash_split[-1]

    return (name, epoch, hyp_hash)

# global 
output_list = []
output_headers = []

# 
model_list = []
model_headers = pickModelFields(sd_models.CheckpointInfo._fields)
#
hypernetwork_list = []
hypernetwork_header = ['name', 'epoch', 'hash']
#
embedding_list = []
embedding_header = []

for model in sd_models.checkpoints_list:
    checkpointInfo = sd_models.checkpoints_list[model]
    model_list.append(list(pickModelFields(checkpointInfo)))
for hypernetwork in hypernetwork.list_hypernetworks(shared.cmd_opts.hypernetwork_dir):
    hypernetworkInfo = parseHypernetworkName(hypernetwork)
    hypernetwork_list.append(hypernetworkInfo)
for embeddings in []:
    pass

output_list = model_list[:]

headers = pickModelFields(sd_models.CheckpointInfo._fields)
selected_option = headers[0]

def populateOutput(search_text):
    return search(search_text, optionToIndex(selected_option))

def search(keyword, header_index):
    final = []
    for model in output_list:
        if keyword in model[header_index].lower():
            final.append(model)

    return dfOutputShape(final, headers)


def optionToIndex(option):
    headers
    if option not in headers:
        raise Exception("Invalid option")

    for i in range(len(headers)):
        if headers[i] == option:
            return i

def setOption(option):
    global selected_option 
    selected_option = option
    return


def swapAsset(asset_name):

    global output_list
    global headers

    if asset_name == Assets[0]:
        output_list = model_list[:]
        # ['hash', 'model_name']
        headers = pickModelFields(sd_models.CheckpointInfo._fields)
    elif asset_name == Assets[1]:
        output_list = hypernetwork_list[:]
        headers = hypernetwork_header
    elif asset_name == Assets[2]:
        output_list = embedding_list[:]
        headers = embedding_header
    

    return dfOutputShape(output_list, headers), gr.Dropdown.update(choices=headers)

# create a dict with keys 'data' & 'headers'
def dfOutputShape(output_list, headers):
    return {
        'data': output_list,
        'headers': headers
    }

hypernetworks_url = '/sdapi/v1/hypernetworks'
models_url = '/sdapi/v1/sd-models'
upscalers = '/sdapi/v1/upscalers'

def on_ui_tabs():
    with gr.Blocks(analytics_enabled=False) as auxiliary_interface:
        with gr.Row().style(equal_height=False):
            with gr.Column(variant='panel'):
                gr.HTML(value="sync resources")
                hypernetwork_button = gr.Button("SYNC")
                # add text box for id input
                # and text for progress, and options for what to sync?
                print(requests.get("http://127.0.0.1:7860/sdapi/v1/hypernetworks"))
        

    return [(auxiliary_interface, tab_title, tab_elem_id)]

script_callbacks.on_ui_tabs(on_ui_tabs)
