import streamlit as st

st.set_page_config(page_title="AI Booking Assistant", layout="wide")

from rag_pipeline import RAGPipeline
from booking_flow import process_message
from admin_dashboard import show_dashboard

if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'rag_pipeline' not in st.session_state:
    st.session_state.rag_pipeline = RAGPipeline()

st.title("AI Booking Assistant")
st.markdown("Upload PDFs for RAG queries or book appointments via chat!")

tab1, tab2 = st.tabs(["Chat", "Admin Dashboard"])
with tab1:
    with st.sidebar:
        st.header("PDF Upload")
        uploaded_files = st.file_uploader(
            "Upload PDFs", accept_multiple_files=True, type="pdf"
        )
        if uploaded_files:
            with st.spinner("Processing..."):
                st.session_state.rag_pipeline.ingest_pdfs(uploaded_files)
                st.success("PDFs ingested!")
        st.info("Say 'book hotel' → Answer questions → 'yes' = SAVE!")

    chat_container = st.container()

    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    prompt = st.chat_input("Ask about services or book an appointment...")

    if prompt:
        # User message
        st.session_state.messages.append(
            {"role": "user", "content": prompt}
        )
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)

        # Assistant response
        with chat_container:
            with st.chat_message("assistant"):
                with st.spinner("AI thinking..."):
                    response = process_message(prompt, st.session_state)
                    st.markdown(response)

        st.session_state.messages.append(
            {"role": "assistant", "content": response}
        )

with tab2:
    show_dashboard()
