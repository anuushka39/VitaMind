"""
CLI: builds the FAISS vector store from data/knowledge_base/*.txt|*.md and
persists it to data/faiss_index/.

Run this once after adding/editing knowledge base files, and again any time
they change. The app itself never reindexes on its own — it only loads
what's already on disk (see app/vectorstore/store.py: get_retriever()).

Usage:
    python scripts/build_faiss_index.py
"""

import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.vectorstore.store import build_vector_store  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

if __name__ == "__main__":
    store = build_vector_store()
    print(f"Saved FAISS index with {store.index.ntotal} vectors to data/faiss_index/.")
