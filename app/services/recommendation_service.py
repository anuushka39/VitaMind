"""
Recommendation service — thin wrapper around the vector store's retriever.

This class doesn't know (and doesn't need to know) that LangChain, FAISS,
or HuggingFace embeddings are involved underneath — it only calls
get_retriever() from app.vectorstore.store and asks it for documents. That
function is the entire seam between this service and the vectorstore
module; swapping FAISS for another LangChain-supported vectorstore later
only touches store.py, never this file.

No Gemini calls here — that responsibility lives in MealService's single
reply-composition pass (one "rewrite naturally" step for the whole meal,
not a separate phrasing call per retrieval).
"""

import logging
from collections.abc import Callable

from app.vectorstore.store import get_retriever

logger = logging.getLogger(__name__)


class RecommendationService:
    def __init__(self, retriever_provider: Callable[[int], object] = get_retriever):
        self._retriever_provider = retriever_provider

    def retrieve_tips(self, detected_food: str, k: int = 3) -> list[str]:
        """
        Returns up to k relevant raw tip strings, most relevant first.
        Empty list if the vector store can't be loaded or built (e.g. no
        knowledge base files present, or the embedding model isn't
        available) -- callers should treat that as "no tips this time,"
        not an error; a retrieval failure should never block meal logging.
        """
        try:
            retriever = self._retriever_provider(k)
            docs = retriever.invoke(f"healthy alternatives to {detected_food}")
        except Exception:
            logger.exception("Tip retrieval failed for %r -- continuing without tips.", detected_food)
            return []
        return [doc.page_content for doc in docs]


recommendation_service = RecommendationService()