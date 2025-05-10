import streamlit as st
from dotenv import load_dotenv
import os
from db import create_tables, register_user, login_user, save_chat, get_user_chats, has_scheduled_meeting, mark_meeting_scheduled
from langchain_groq import ChatGroq
from langchain.chains import RetrievalQA
from langchain.document_loaders import PyPDFLoader
from langchain.indexes import VectorstoreIndexCreator
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate
import time

# Load environment
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")
model = "meta-llama/llama-4-scout-17b-16e-instruct"
pdf_path = "data.pdf"
calendly_link = "https://calendly.com/jawadthewebdeveloper"  # Your Calendly link

# Setup
st.set_page_config(page_title="AI Agency Chatbot", layout="wide")
st.title("🤖 Agency Assistant")

# Create DB tables
create_tables()

# Session states
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = None
if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None
if "scheduled" not in st.session_state:
    st.session_state.scheduled = False

# Load PDF
@st.cache_resource
def load_vectorstore():
    loader = [PyPDFLoader(pdf_path)]
    index = VectorstoreIndexCreator(
        embedding=HuggingFaceEmbeddings(model_name='all-MiniLM-L12-v2'),
        text_splitter=RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    ).from_loaders(loader)
    return index.vectorstore

# Auth Interface (Only shows if user is not authenticated)
if not st.session_state.authenticated:
    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        st.subheader("🔐 Login")
        login_username = st.text_input("Username", key="login_username")
        login_password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login"):
            if login_user(login_username, login_password):
                st.success("Logged in!")
                st.session_state.authenticated = True
                st.session_state.username = login_username
                st.session_state.vectorstore = load_vectorstore()
            else:
                st.error("Invalid credentials.")

    with tab2:
        st.subheader("📝 Register")
        register_username = st.text_input("New Username", key="reg_username")
        register_password = st.text_input("New Password", type="password", key="reg_password")
        if st.button("Register"):
            if register_user(register_username, register_password):
                st.success("Registered successfully! Please login.")
            else:
                st.error("User already exists.")
else:
    # If already authenticated, show the chatbot interface
    username = st.session_state.username
    st.markdown(f"Welcome, **{username}**")

    # Check if user has a scheduled meeting
    if has_scheduled_meeting(username):
        # Show the option to reschedule the meeting with a clickable link
        if st.button("📅 Reschedule Meeting"):
            st.markdown(f"You can now reschedule your meeting by clicking [here]({calendly_link})")
        else:
            st.info("✅ Meeting has been scheduled. You can continue chatting.")
    
    else:
        # Show the option to schedule a meeting
        if st.button("📅 Schedule a Meeting"):
            mark_meeting_scheduled(username)
            st.markdown(f"You can schedule your meeting by clicking [here]({calendly_link})")
            time.sleep(1)

    # Initialize chat history from DB
    history = get_user_chats(username)
    for q, a in history:
        with st.chat_message("user"):
            st.markdown(q)
        with st.chat_message("assistant"):
            st.markdown(a)

    # Input box for user to ask questions
    user_input = st.chat_input("Ask me anything...")
    if user_input:
        with st.chat_message("user"):
            st.markdown(user_input)

        groq_chat = ChatGroq(groq_api_key=groq_api_key, model_name=model)

        prompt_template = ChatPromptTemplate.from_template(""" 
        You are an expert AI assistant. Answer this: {query}
        Be clear, concise, and helpful. Skip small talk.
        """)

        if not st.session_state.vectorstore:
            st.session_state.vectorstore = load_vectorstore()

        qa_chain = RetrievalQA.from_chain_type(
            llm=groq_chat,
            chain_type="stuff",
            retriever=st.session_state.vectorstore.as_retriever(search_kwargs={'k': 3}),
            return_source_documents=False
        )

        try:
            result = qa_chain({"query": user_input})
            answer = result["result"]
            if not answer or len(answer.strip()) < 30:
                messages = prompt_template.format_messages(query=user_input)
                answer = groq_chat.invoke(messages).content
        except Exception as e:
            answer = f"Sorry, I couldn't fetch the answer due to: {str(e)}"

        with st.chat_message("assistant"):
            st.markdown(answer)

        # Save conversation to database
        save_chat(username, user_input, answer)
