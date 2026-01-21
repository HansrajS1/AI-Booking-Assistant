import os
import streamlit as st
from langchain_community.embeddings import HuggingFaceEmbeddings  
from langchain_community.vectorstores import FAISS             
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain_groq import ChatGroq
from langchain_community.document_loaders import PyMuPDFLoader  
import tempfile
from config import GROQ_API_KEY


class RAGPipeline:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        self.llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)
        self.vector_store = None
        self.documents = []
    
    def ingest_pdfs(self, pdf_files):
        st.info(f" Processing {len(pdf_files)} PDF(s)...")
        
        self.documents = []
        self.vector_store = None
        
        for i, pdf_file in enumerate(pdf_files):
            try:
                pdf_bytes = pdf_file.read()
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    tmp_file.write(pdf_bytes)
                    tmp_path = tmp_file.name
                loader = PyMuPDFLoader(tmp_path)
                docs = loader.load()
                
                splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1000, 
                    chunk_overlap=200
                )
                splits = splitter.split_documents(docs)
                self.documents.extend(splits)
                
                st.success(f" {pdf_file.name} → {len(splits)} chunks")
                
            except Exception as e:
                st.error(f" {pdf_file.name}: {str(e)}")
            finally:
                if 'tmp_path' in locals():
                    os.unlink(tmp_path)
        
        if self.documents:
            self.vector_store = FAISS.from_documents(self.documents, self.embeddings)
            st.success(f"RAG READY! {len(self.documents)} chunks indexed!")
            return True
        return False
    
    def query(self, question: str):
        if not self.vector_store:
            return " Upload PDFs first (sidebar) → Click PROCESS → Ask questions!"
        
        prompt_template = """
        You are a helpful service assistant. Answer using ONLY the PDF context below.

        CONTEXT: {context}

        QUESTION: {question}

        If question mentions booking → end with: "Say 'book [service]' to book now!"

        Answer concisely:
        """

        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vector_store.as_retriever(search_kwargs={"k": 4}),
            chain_type_kwargs={"prompt": prompt_template}
        )
        
        result = qa_chain.run(question)
        return result
