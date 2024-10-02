"""
Teaching Assistant Chatbot

This module provides a user interface for a teaching assistant chatbot using Streamlit.
The chatbot is designed to assist students with answering questions and providing explanations.
The chatbot uses the OpenAI GPT-3 model to generate responses based on the input questions and the
context of the course documents. The course documents are indexed using the LLAMA Indexing Library
and stored in a vector database for efficient retrieval.

Author: Ali Shiraee
Last Modified: October 1st, 2024
"""

import json
import os
import sys
__import__("pysqlite3")
sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")
import sqlite3

from pathlib import Path
import streamlit as st
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import Settings
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.vector_stores.chroma import ChromaVectorStore
import openai
import chromadb
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader


def is_unchanged(docs_path, vectordb_path):
    """
    Check if the documents in the docs_path have changed since the last indexing.

    Args:

    docs_path (str): The path to the directory containing the documents.
    vectordb_path (str): The path to the directory containing the vector database.
    """
    directory = Path(docs_path)
    all_files = list(directory.rglob("*.*"))
    current_files = [file.name for file in all_files]

    db = chromadb.PersistentClient(path=vectordb_path)
    chroma_collection = db.get_or_create_collection("documents")
    all_saved_docs = chroma_collection.get()
    previous_files = {x["file_name"] for x in all_saved_docs["metadatas"]}
    return previous_files == set(current_files)


with open("assistant_config.json", encoding="utf-8") as f:
    json_config = json.load(f)
config = yaml.load(st.secrets.yaml.content, Loader=SafeLoader)

Settings.llm = OpenAI(model=json_config["model"])
Settings.temperature = json_config["temperature"]
Settings.system_prompt = json_config["system_prompt"]
Settings.embed_model = OpenAIEmbedding(model=json_config["embed_model"])
Settings.node_parser = SentenceSplitter(
    chunk_size=json_config["chunk_size"], chunk_overlap=json_config["chunk_overlap"]
)

st.set_page_config(
    page_title=json_config["name"],
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="auto",
    menu_items=None,
)

authenticator = stauth.Authenticate(
    config["credentials"],
    config["cookie"]["name"],
    config["cookie"]["key"],
    config["cookie"]["expiry_days"],
)

authenticator.login(location="sidebar")

if st.session_state["authentication_status"] is False:
    st.error("Username/password is incorrect")
elif st.session_state["authentication_status"] is None:
    st.title(json_config["name"])
    st.warning("Please enter your username and password to proceed.")
else:

    openai.api_key = os.getenv("OPENAI_API_KEY")
    st.title(json_config["name"])
    st.info(
        "AI can make mistakes, make sure to double-check important information.",
        icon="⚠️",
    )
    if "messages" not in st.session_state.keys():
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "I can answer your questions about the course "
                    "material, exams, outlines, and other course details. Ask me anything!"
                ),
            }
        ]
    with st.sidebar:
        st.image("./assets/m24-rev_png.png")
        st.write(f'Welcome *{st.session_state["name"]}*')
        st.markdown(
            (
                f"This is your personal teaching assistant for the **{json_config['course_name']}**"
                " course. You can access the course content "
                "[here](https://avenue.cllmcmaster.ca/d2l/le/content/596841/Home)"
            )
        )
        authenticator.logout("Logout", "main")

    @st.cache_resource(show_spinner=False)
    def create_index():
        """
        Load and index documents for the first time and save them into the vector store.

        Returns:
        VectorStoreIndex: The index created from the documents in the docs_path.
        """
        with st.spinner(
            text="Loading and indexing documents for the first time"
            "– hang tight! This might take 1-2 minutes."
        ):
            reader = SimpleDirectoryReader(
                input_dir=json_config["docs_path"], recursive=True
            )
            docs = reader.load_data()
            db = chromadb.PersistentClient(path=json_config["vectordb_path"])
            chroma_collection = db.get_or_create_collection("documents")
            vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
            return VectorStoreIndex.from_documents(
                docs, storage_context=storage_context
            )

    @st.cache_resource(show_spinner=False)
    def load_index():
        """
        Load the index from the existing vector store.

        Returns:
        VectorStoreIndex: The index loaded from the existing vector store.
        """
        db = chromadb.PersistentClient(path=json_config["vectordb_path"])
        chroma_collection = db.get_or_create_collection("documents")
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        return VectorStoreIndex.from_vector_store(vector_store)

    if (
        os.path.exists(json_config["vectordb_path"])
        and os.listdir(json_config["vectordb_path"])
        and is_unchanged(json_config["docs_path"], json_config["vectordb_path"])
    ):
        index = load_index()
    else:
        index = create_index()

    if "chat_engine" not in st.session_state.keys():
        memory = ChatMemoryBuffer.from_defaults(token_limit=3900)
        st.session_state.chat_engine = index.as_chat_engine(
            chat_mode="condense_plus_context",
            memory=memory,
            context_prompt=(
                "You are an AI teaching assistant, able to answer questions about"
                " course material, exams, outlines, and other course details."
                " Here are the relevant documents for the context:\n"
                "{context_str}"
                "\nInstruction: Based on the above documents, provide a detailed answer for the"
                " student question below. If there is no relevant information in the documents,"
                " inform the student that no related information was found in the course database"
                " and refuse to answer the question."
            ),
            verbose=True,
        )

    if prompt := st.chat_input("Type your question..."):
        st.session_state.messages.append({"role": "user", "content": prompt})

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    if st.session_state.messages[-1]["role"] != "assistant":
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = st.session_state.chat_engine.chat(prompt)
                if response.source_nodes and response.source_nodes[0].score > 0.3:
                    relevant_node = response.source_nodes[0]
                    # page {relevant_node.metadata["page_label"]}'
                    SOURCE_STRING = (
                        f'<b>Source:</b> file "{relevant_node.metadata["file_name"]}"'
                    )
                    SOURCE_HTML = f'<br><br><span style="font-size:0.75rem;">{SOURCE_STRING}</span>'
                else:
                    print(f"success, nodes: {response.source_nodes}")
                    SOURCE_HTML = ""

                HTML_STRING = f"""
                <div>
                    {response.response}{SOURCE_HTML}
                </div>
                """
                st.write(HTML_STRING, unsafe_allow_html=True)
                message = {"role": "assistant", "content": response.response}
                st.session_state.messages.append(message)
