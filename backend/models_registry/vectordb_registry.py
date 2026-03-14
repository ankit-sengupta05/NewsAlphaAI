"""
backend/models_registry/vectordb_registry.py
Thin factory that returns a LangChain-compatible vector store.
"""
from __future__ import annotations

from functools import lru_cache

from langchain_core.vectorstores import VectorStore
from langchain_community.embeddings import HuggingFaceEmbeddings

from backend.core.config import settings


@lru_cache(maxsize=1)
def get_embeddings() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(model_name=settings.embedding_model)


@lru_cache(maxsize=4)
def get_vectorstore(collection: str = "news") -> VectorStore:
    """
    Return a vector store for the given collection name.
    Backed by Chroma (default) or FAISS depending on config.
    """
    embeddings = get_embeddings()

    if settings.vectordb_provider == "chroma":
        from langchain_community.vectorstores import Chroma
        return Chroma(
            collection_name=collection,
            embedding_function=embeddings,
            persist_directory=str(settings.chroma_persist_dir),
        )

    elif settings.vectordb_provider == "faiss":
        from langchain_community.vectorstores import FAISS
        index_path = settings.faiss_index_dir / collection
        if index_path.exists():
            return FAISS.load_local(str(index_path), embeddings,
                                    allow_dangerous_deserialization=True)
        # Bootstrap an empty FAISS store with a dummy doc that we delete later
        store = FAISS.from_texts(["__init__"], embeddings)
        store.save_local(str(index_path))
        return store

    raise ValueError(f"Unknown vectordb provider: {settings.vectordb_provider}")
