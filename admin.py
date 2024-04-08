import streamlit as st
import pandas as pd
from io import StringIO
import tempfile
import os
import json
import time
import pandas as pd



with open("assistant_config.json") as f:
    json_config = json.load(f)

def list_files(directory):
    files = os.listdir(directory)
    return files

def remove_file_from_directory(file_name, directory):
    os.remove(os.path.join(directory, file_name))

def delete_file(directory, filename, col_filename, col_delete):
    filepath = os.path.join(directory, filename)
    print('REMOVING: ', filepath)
    if os.path.exists(filepath):
        os.remove(filepath)
        col_filename.empty()
        col_delete.empty()
        del col_filename
        del col_delete 
        st.success(f"Deleted {filename}")

    else:
        st.error(f"File {filename} not found")




def update_file_list(container):
    print('CALLING UPDATE FILE LIST')
    file_list = list_files(docs_path)

    for filename in file_list:

        # create columns with borders
        col_filename, col_delete = container.columns((2, 1))
        col_filename.write(filename)
        # placeholder = col_delete.empty()
        # placeholder.button(f"Delete {filename}", key=filename, on_click=delete_file, args=(docs_path, filename, col_filename, placeholder))
       

def show_added_file(filename, container):
    col_filename, col_delete = container.columns((2, 1))
    col_filename.write(filename)
    placeholder = col_delete.empty()
    # placeholder.button("Delete", key=filename, on_click=delete_file, args=(docs_path, filename, col_filename, placeholder))
    

st.set_page_config(page_title=json_config["name"],
                   page_icon="🤖", layout="centered", initial_sidebar_state="auto", menu_items=None)
            
docs_path = json_config['docs_path']

container = st.container(border=True)

# if 'state' not in st.session_state:
#     st.session_state['state'] = 'initial'
#     print('INITIALIZING SETTING STATE= ', st.session_state['state'])
#     update_file_list(container)
# elif st.session_state['state'] == 'initial': 
#     st.session_state['state'] = 'running'
# else:
#     print('CHECKING SESSION STATE= ', st.session_state['state'])


update_file_list(container)
uploaded_file = st.file_uploader("Choose academic resources and files to add to the data directory:")




if uploaded_file is not None:
    temp_dir = tempfile.mkdtemp()
    path = os.path.join(temp_dir, uploaded_file.name)

    print('path= ', path)
    
    save_path = os.path.join(docs_path, uploaded_file.name)
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getvalue())
    # st.write(uploaded_file.name)
    show_added_file(uploaded_file.name, container)
    uploaded_file = None
    print('uploaded_file= ', uploaded_file)

