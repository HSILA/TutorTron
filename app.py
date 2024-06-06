import streamlit as st
from database import get_user_credentials, insert_chat_history, load_index_from_db, save_index_in_db
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import Settings
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
import openai
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import dotenv
import json
import os


with open("assistant_config.json") as f:
    json_config = json.load(f)
with open('./users.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

Settings.llm = OpenAI(model=json_config['model'])
Settings.temperature = json_config['temperature']
Settings.system_prompt = json_config['system_prompt']
Settings.embed_model = OpenAIEmbedding(model=json_config['embed_model'])
Settings.node_parser = SentenceSplitter(
    chunk_size=json_config['chunk_size'], chunk_overlap=json_config['chunk_overlap'])

st.set_page_config(page_title=json_config["name"],
                   page_icon="🤖", layout="centered", initial_sidebar_state="auto", menu_items=None)

user_credentials = get_user_credentials()
authenticator = stauth.Authenticate(
    user_credentials,
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['pre-authorized']
)

authenticator.login()

if st.session_state["authentication_status"] is False:
    st.error('Username/password is incorrect')
elif st.session_state["authentication_status"] is None:
    st.warning('Please enter your username and password')
else:

    openai.api_key = dotenv.get_key('.env', 'OPENAI_API_KEY')
    st.title(json_config["name"])
    st.info(
        f"{json_config['name']} can make mistakes, make sure to check important information.", icon="⚠️")

    if "messages" not in st.session_state.keys():
        st.session_state.messages = [
            {"role": "assistant",
                "content": f"I am  your personal teaching assistant for the {json_config['course_name']} course. I can answer questions about the course material. Ask me anything!"}
        ]

    @st.cache_resource(show_spinner=False)
    def load_data():
        with st.spinner(text="Loading and indexing documents – hang tight! This might take 1-2 minutes."):
            reader = SimpleDirectoryReader(
                input_dir=json_config["docs_path"], recursive=True)
            docs = reader.load_data(num_workers=os.cpu_count())
            index = VectorStoreIndex.from_documents(docs)
            return index
    index,index_flag=load_index_from_db()
    if not index_flag:
        print("Index does not exist in db")
        index = load_data()
        save_index_in_db(index)
        print('Index saved in db')
        index_flag=True
    else:
        print("Index is read from db")
    

    if "chat_engine" not in st.session_state.keys():
        st.session_state.chat_engine = index.as_chat_engine(
            chat_mode="condense_question", verbose=True)

    if prompt := st.chat_input("Type your question..."):
        st.session_state.messages.append({"role": "user", "content": prompt})

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    if st.session_state.messages[-1]["role"] != "assistant":
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = st.session_state.chat_engine.chat(prompt)
                st.write(response.response)
                message = {"role": "assistant", "content": response.response}
                st.session_state.messages.append(message)
