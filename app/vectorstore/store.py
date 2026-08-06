"""
Vector store for VitaMind's nutrition knowledge base.

This replaces the earlier hand-rolled embedder.py + faiss_index.py +
knowledge_loader.py with LangChain's own abstractions. This project is a
FastAPI backend with a small RAG component, not an ML project, so there's
no reason to maintain a custom embedding wrapper or a custom FAISS wrapper
when DirectoryLoader + RecursiveCharacterTextSplitter + HuggingFaceEmbeddings
+ FAISS already do exactly this, correctly, with far less code to own.

Public surface is three functions — that's the whole contract the rest of
the app depends on:
    build_vector_store()  -- (re)index data/knowledge_base/*.txt|*.md
    load_vector_store()   -- load a previously built index, or None
    get_retriever()        -- what services actually call

Import-time cost is deliberately near zero: LangChain's imports (and the
sentence-transformers -> transformers -> torch chain behind
HuggingFaceEmbeddings) happen INSIDE each function, not at module top
level. That's not a lazy-loading hack for its own sake — it's what makes
"a broken/missing torch install should degrade the recommendation feature,
not take down the whole API" actually true. If FAISS/HuggingFaceEmbeddings
were imported at the top of this file, simply importing app.main (which
every request goes through) would hard-fail whenever that heavy, ML-shaped
dependency chain has a problem — exactly the kind of import-time blocking
this project's own scope explicitly warns against.
"""

import logging
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from langchain_community.vectorstores import FAISS
    from langchain_core.vectorstores import VectorStoreRetriever
    from langchain_huggingface import HuggingFaceEmbeddings

logger = logging.getLogger(__name__)

KNOWLEDGE_BASE_DIR = "data/knowledge_base"
INDEX_DIR = "data/faiss_index"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

_embeddings: "HuggingFaceEmbeddings | None" = None


def _get_embeddings() -> "HuggingFaceEmbeddings":
    """
    Model load is the expensive part (a few seconds) -- cached so it
    happens once per process, the first time it's actually needed.
    """
    global _embeddings
    if _embeddings is None:
        from langchain_huggingface import HuggingFaceEmbeddings

        _embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    return _embeddings


def _load_documents(knowledge_dir: str) -> list:
    """Loads every .txt and .md file under knowledge_dir. Two DirectoryLoader
    passes (one per extension) rather than one clever combined glob — a
    glob pattern that matches both 2- and 3-character extensions correctly
    isn't simpler, it's just harder to read."""
    from langchain_community.document_loaders import DirectoryLoader, TextLoader

    documents = []
    for pattern in ("**/*.txt", "**/*.md"):
        loader = DirectoryLoader(
            knowledge_dir,
            glob=pattern,
            loader_cls=TextLoader,
            loader_kwargs={"encoding": "utf-8"},
        )
        documents.extend(loader.load())
    return documents


def build_vector_store(
    knowledge_dir: str = KNOWLEDGE_BASE_DIR, index_dir: str = INDEX_DIR
) -> "FAISS":
    """
    Loads the knowledge base, chunks it, embeds it, and persists a FAISS
    index to disk. This is the only place indexing happens — the app
    itself never re-indexes on its own; it only loads what's already built
    (see get_retriever()). Run via scripts/build_faiss_index.py whenever
    data/knowledge_base/ changes.
    """
    from langchain_community.vectorstores import FAISS
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    documents = _load_documents(knowledge_dir)
    if not documents:
        raise ValueError(f"No .txt/.md files found in {knowledge_dir}")

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(documents)

    store = FAISS.from_documents(chunks, _get_embeddings())
    store.save_local(index_dir)
    logger.info(
        "Built FAISS index: %d chunks from %d files -> %s", len(chunks), len(documents), index_dir
    )
    return store


def load_vector_store(index_dir: str = INDEX_DIR) -> "FAISS | None":
    """
    Loads a previously built index, or returns None if it doesn't exist.
    allow_dangerous_deserialization=True is required by LangChain's FAISS
    loader because loading unpickles the stored docstore — safe here since
    the index is one this project builds itself, never one accepted from
    an untrusted source.
    """
    if not os.path.exists(index_dir):
        return None

    from langchain_community.vectorstores import FAISS

    return FAISS.load_local(index_dir, _get_embeddings(), allow_dangerous_deserialization=True)


def get_retriever(k: int = 3) -> "VectorStoreRetriever":
    """
    The one function the rest of the app should call (see
    RecommendationService). Loads the persisted index if it exists;
    builds and saves one on the spot if it doesn't (e.g. first run on a
    fresh clone). Callers get back a standard LangChain retriever and never
    need to know FAISS, embeddings, or chunking are involved at all.
    """
    store = load_vector_store()
    if store is None:
        logger.warning("No FAISS index found at %s -- building one now.", INDEX_DIR)
        store = build_vector_store()
    return store.as_retriever(search_kwargs={"k": k})
