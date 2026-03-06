"""
rag_system.py — PolicyRAG: Retrieval-Augmented Generation for insurance policy Q&A.
Uses LangChain, FAISS, HuggingFace embeddings, and the Groq LLM.
"""

import os
from typing import List

from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, TextLoader, PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_groq import ChatGroq

load_dotenv()


class PolicyRAG:
    """
    Policy Retrieval-Augmented Generation system.

    Loads insurance policy documents, builds a FAISS vector store,
    and answers natural-language questions using a Groq-backed LLM.
    """

    def __init__(self):
        """Initialise the RAG system (vectorstore is built lazily)."""
        self.documents: List = []
        self.vectorstore = None
        self.chain = None
        self.chat_history: List = []
        api_key = os.getenv("GROQ_API_KEY")
        self.llm = ChatGroq(
            model="llama-3.1-8b-instant",
            api_key=api_key,
            temperature=0.2,
        )

    # ------------------------------------------------------------------
    def load_documents(self, folder_path: str) -> None:
        """
        Load all .txt and .pdf files from *folder_path*.

        Args:
            folder_path: Relative or absolute path to the folder containing
                         policy documents.
        """
        self.documents = []
        try:
            # Load .txt files
            txt_loader = DirectoryLoader(
                folder_path,
                glob="**/*.txt",
                loader_cls=TextLoader,
                loader_kwargs={"encoding": "utf-8"},
                show_progress=False,
            )
            self.documents.extend(txt_loader.load())

            # Load .pdf files
            pdf_loader = DirectoryLoader(
                folder_path,
                glob="**/*.pdf",
                loader_cls=PyPDFLoader,
                show_progress=False,
            )
            self.documents.extend(pdf_loader.load())

            print(f"  Loaded {len(self.documents)} document(s) from '{folder_path}'.")
        except Exception as exc:
            print(f"  [ERROR] Failed to load documents: {exc}")

    # ------------------------------------------------------------------
    def build_vectorstore(self) -> None:
        """
        Split loaded documents and build a FAISS vector store with
        HuggingFace 'all-MiniLM-L6-v2' embeddings.
        """
        try:
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=50,
            )
            chunks = splitter.split_documents(self.documents)
            print(f"  Split into {len(chunks)} chunk(s).")

            embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
            self.vectorstore = FAISS.from_documents(chunks, embeddings)
            print("  Vectorstore built successfully.")

            # Build LCEL retrieval chain
            retriever = self.vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 4},
            )

            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a helpful insurance policy assistant. Use the context below to answer the question accurately and concisely.\n\nContext:\n{context}"),
                ("human", "{question}"),
            ])

            def format_docs(docs):
                return "\n\n".join(d.page_content for d in docs)

            self.chain = (
                {"context": retriever | format_docs, "question": RunnablePassthrough()}
                | prompt
                | self.llm
                | StrOutputParser()
            )
        except Exception as exc:
            print(f"  [ERROR] Failed to build vectorstore: {exc}")

    # ------------------------------------------------------------------
    def answer(self, question: str) -> str:
        """
        Answer a question about the loaded policy using RAG.

        Args:
            question: Natural-language question about the policy.

        Returns:
            The LLM's answer as a string, or an error message.
        """
        if self.chain is None:
            return "Vectorstore not built yet. Call build_vectorstore() first."
        try:
            answer = self.chain.invoke(question)
            self.chat_history.append((question, answer))
            return answer
        except Exception as exc:
            return f"[ERROR] Could not retrieve answer: {exc}"
