import streamlit as st
# from llama_index import VectorStoreIndex, ServiceContext
from llama_index.core import VectorStoreIndex,SimpleDirectoryReader,ServiceContext
# from llama_index.core.memory import ChatMemoryBuffer
from llama_index.llms.openai import OpenAI
import openai
# from llama_index import SimpleDirectoryReader
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import dotenv
import json

from database import get_user_credentials, insert_chat_history


with open("assistant_config.json") as f:
    json_config = json.load(f)
with open('./users.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)


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
            docs = reader.load_data()
            service_context = ServiceContext.from_defaults(llm=OpenAI(
                model="gpt-3.5-turbo", temperature=json_config['temperature'], system_prompt=json_config['system_prompt']))
            index = VectorStoreIndex.from_documents(
                docs, service_context=service_context)
            return index

    index = load_data()
    # memory = ChatMemoryBuffer.from_defaults(token_limit=5000)
    if "chat_engine" not in st.session_state.keys():
        st.session_state.chat_engine = index.as_chat_engine(
            # chat_mode="condense_plus_context", memory=memory, verbose=True)
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
                # if 'username' in st.session_state:
                #     insert_chat_history(st.session_state['username'], prompt, response.response)
                # print(memory.get_all())