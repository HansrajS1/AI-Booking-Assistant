import os
import streamlit as st
from langchain_community.embeddings import HuggingFaceEmbeddings  
from langchain_community.vectorstores import FAISS             
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain_groq import ChatGroq
from langchain_community.document_loaders import PyMuPDFLoader  
from langchain.prompts import PromptTemplate
import tempfile
from config import GROQ_API_KEY

os.environ["GROQ_API_KEY"] = GROQ_API_KEY

class RAGPipeline:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        self.llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)
        self.vector_store = None
        self.qa_chain = None

    def ingest_pdfs(self, pdf_files):
        st.info(f" Processing {len(pdf_files)} PDF(s)...")
        documents = []

        for pdf_file in pdf_files:
            tmp_path = None
            try:
                pdf_bytes = pdf_file.read()
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    tmp_file.write(pdf_bytes)
                    tmp_path = tmp_file.name

                loader = PyMuPDFLoader(tmp_path)
                docs = loader.load()

                splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                documents.extend(splitter.split_documents(docs))
                st.success(f" {pdf_file.name} → {len(docs)} pages, {len(splitter.split_documents(docs))} chunks")
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        if not documents:
            st.warning("No text extracted from PDFs.")
            return False

        self.vector_store = FAISS.from_documents(documents, self.embeddings)

        prompt = PromptTemplate(
            input_variables=["context", "question"],
            template="""
You are a helpful service assistant. Answer using ONLY the PDF context below.

CONTEXT:
{context}

QUESTION:
{question}

If question mentions booking, end with: "Say 'book [service]' to book now!"

Answer concisely.
"""
        )

        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            retriever=self.vector_store.as_retriever(search_kwargs={"k": 4}),
            chain_type="stuff",
            chain_type_kwargs={"prompt": prompt}
        )

        st.success(f"RAG READY! {len(documents)} chunks indexed!")
        return True

    def query(self, question: str):
        if not self.qa_chain:
            return " Upload PDFs first → Click PROCESS → Ask questions!"
        try:
            return self.qa_chain.run(question)
        except Exception as e:
            st.error(f"Groq API error: {str(e)}")
            return "Error querying the LLM. Check your API key or PDF content."
