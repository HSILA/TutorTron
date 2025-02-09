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

import os
import streamlit as st
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core import Settings
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
import openai
import streamlit_authenticator as stauth
from users.user_handler import fetch_users
from src.index import load_index


def clear_chat_history():
    """
    Clear the chat history by resetting the messages in the session state.
    """
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "I can answer your questions about the course "
                "material, exams, outlines, and other course details. Ask me anything!"
            ),
        }
    ]


CHATBOT_SETTINGS = st.secrets["chatbot_settings"]
auth_config = fetch_users()

Settings.llm = OpenAI(model=CHATBOT_SETTINGS["llm"])
Settings.temperature = CHATBOT_SETTINGS["temperature"]
Settings.system_prompt = CHATBOT_SETTINGS["system_prompt"]
Settings.embed_model = OpenAIEmbedding(model=CHATBOT_SETTINGS["embedding"])

st.set_page_config(
    page_title=CHATBOT_SETTINGS["chatbot_name"],
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="auto",
    menu_items=None,
)

authenticator = stauth.Authenticate(
    auth_config["credentials"],
    auth_config["cookie"]["name"],
    auth_config["cookie"]["key"],
    auth_config["cookie"]["expiry_days"],
)

authenticator.login(location="sidebar")

if st.session_state["authentication_status"] is False:
    st.error("Username/password is incorrect")
elif st.session_state["authentication_status"] is None:
    st.title(CHATBOT_SETTINGS["chatbot_name"])
    st.warning("Please enter your username and password to proceed.")
else:

    openai.api_key = os.getenv("OPENAI_API_KEY")
    st.title(CHATBOT_SETTINGS["chatbot_name"])
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
                f"This is your assistant for the **{CHATBOT_SETTINGS['course_name']}**"
                " course. You can access the course content "
                "[here](https://avenue.cllmcmaster.ca/d2l/le/content/596841/Home)."
            )
        )
        authenticator.logout("Logout", "main")
        st.sidebar.button("Clear Chat History", on_click=clear_chat_history)
        FOOTER_HTML = """<br><br><br><br>
        <a href="https://mahyarh.com/" style="text-decoration: none;">
            <div style="text-align: center;">
                <p>Powered by MahyarLab</p>
            </div>
        </a>"""
        st.markdown(FOOTER_HTML, unsafe_allow_html=True)

    @st.cache_resource(show_spinner=False)
    def _load_index():
        return load_index(CHATBOT_SETTINGS['pinecone_index'])

    index = _load_index()

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
