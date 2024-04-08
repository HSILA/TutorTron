import streamlit as st
import pandas as pd
from io import StringIO
import tempfile
import os
import json
import time




def change_config_file(temperature, data_path):
    with open("assistant_config.json") as f:
        json_config = json.load(f)
    json_config['temperature'] = temperature
    json_config['docs_path'] = data_path
    with open("assistant_config.json", "w") as f:
        json.dump(json_config, f)
    st.success("Configuration updated. Please clear cache and rerun the assistant.")


def change_config_page():
    import streamlit as st
    st.write(
            """
            You can change the assistant's configuration.
    """
        )
    data_path = st.text_input("Data Directory:", value="data")
    print('TEXT= ', data_path)
    # create directory if it does not exist
    
    temperature = st.slider('Temperature', min_value=0.0, max_value=1.0, step=0.1)
    print('TEMPERATURE= ', temperature)
    submitted = st.button("Update Configuration")
    if submitted:
        change_config_file(temperature, data_path)
        if not os.path.exists(data_path):
            os.makedirs(data_path)
            st.success(f"Created directory {data_path}")



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
        st.session_state['buttons'].discard(filename)
        st.success(f"Deleted {filename}")

    else:
        st.error(f"File {filename} not found")




def update_file_list(container,docs_path):
    print('CALLING UPDATE FILE LIST')
    file_list = list_files(docs_path)
    existing_files_and_buttons = [filename for filename in st.session_state['buttons']]
    print('EXISTING FILES AND BUTTONS= ', existing_files_and_buttons)
    for filename in file_list:
        
        # create columns for filename and delete button
        col_filename, col_delete = container.columns((2, 1))
        col_filename.write(filename)
        # if filename in existing_files_and_buttons:
        #     print('FILE BUTTON ALREADY EXISTS= ', filename)
        # else:
        placeholder = col_delete.empty()
        placeholder.button(f"Delete {filename}", on_click=delete_file, args=(docs_path, filename, col_filename, placeholder))
        st.session_state['buttons'].add(filename)
       

def show_added_file(filename, container,docs_path):
    col_filename, col_delete = container.columns((2, 1))
    col_filename.write(filename)
    placeholder = col_delete.empty()
    placeholder.button("Delete", on_click=delete_file, args=(docs_path, filename, col_filename, placeholder))
    st.session_state['buttons'].add(filename)
    

def file_upload_page():
    
    with open("assistant_config.json") as f:
        json_config = json.load(f)
    

    docs_path = json_config['docs_path']

    container = st.container(border=True)

    if 'buttons' not in st.session_state:
        st.session_state['buttons'] = set()
    update_file_list(container,docs_path=docs_path)
    with st.form('admin-form', clear_on_submit=True):
        uploaded_file = st.file_uploader("Choose academic resources and files to add to the data directory:")
        submitted = st.form_submit_button("UPLOAD!")

        if submitted and uploaded_file is not None:


            temp_dir = tempfile.mkdtemp()
            path = os.path.join(temp_dir, uploaded_file.name)
            file_list = list_files(docs_path)
            if uploaded_file.name in file_list:
                st.error(f"File {uploaded_file.name} already exists")
                uploaded_file = None
                print('uploaded_file= ', uploaded_file)
            else:
                print('path= ', path)
                
                save_path = os.path.join(docs_path, uploaded_file.name)
                with open(save_path, "wb") as f:
                    f.write(uploaded_file.getvalue())
                # st.write(uploaded_file.name)
                show_added_file(uploaded_file.name, container, docs_path)
                uploaded_file = None
                print('uploaded_file= ', uploaded_file)

page_names_to_funcs = {
    "File Upload": file_upload_page,
    "Config Change": change_config_page
}
with open("assistant_config.json") as f:
        json_config = json.load(f)
st.set_page_config(page_title=json_config["name"],
                    page_icon="🤖", layout="centered", initial_sidebar_state="auto", menu_items=None)
demo_name = st.sidebar.selectbox("Choose a page", page_names_to_funcs.keys())
page_names_to_funcs[demo_name]()
