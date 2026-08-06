"""
RecommendationService.retrieve_tips, tested against a fake retriever
provider — no real vector store, FAISS index, or downloaded embedding
model needed. RecommendationService only ever calls .invoke(query) on
whatever get_retriever(k) hands back, so a fake object with that one
method is a faithful stand-in for LangChain's real retriever here.
"""

from app.services.recommendation_service import RecommendationService


class _FakeDocument:
    def __init__(self, page_content: str):
        self.page_content = page_content


class _FakeRetriever:
    def __init__(self, docs: list[_FakeDocument]):
        self._docs = docs

    def invoke(self, query: str):
        return self._docs


def test_retrieve_tips_returns_raw_text_list():
    fake_docs = [_FakeDocument("Swap fried snacks for roasted chickpeas.")]
    service = RecommendationService(retriever_provider=lambda k: _FakeRetriever(fake_docs))

    tips = service.retrieve_tips("pakora", k=1)

    assert tips == ["Swap fried snacks for roasted chickpeas."]


def test_retrieve_tips_preserves_retriever_order():
    fake_docs = [_FakeDocument("tip one"), _FakeDocument("tip two"), _FakeDocument("tip three")]
    service = RecommendationService(retriever_provider=lambda k: _FakeRetriever(fake_docs))

    tips = service.retrieve_tips("fried chicken", k=3)

    assert tips == ["tip one", "tip two", "tip three"]


def test_retrieve_tips_passes_k_through_to_retriever_provider():
    calls = []

    def fake_provider(k):
        calls.append(k)
        return _FakeRetriever([])

    service = RecommendationService(retriever_provider=fake_provider)
    service.retrieve_tips("pakora", k=5)

    assert calls == [5]


def test_retrieve_tips_returns_empty_list_when_retriever_unavailable():
    """
    Simulates get_retriever() failing -- e.g. no knowledge base files on
    disk yet, or the embedding model isn't installed. Retrieval failures
    must degrade gracefully to "no tips," never raise up into MealService
    and block the meal from being logged.
    """

    def broken_provider(k):
        raise FileNotFoundError("no knowledge base files found")

    service = RecommendationService(retriever_provider=broken_provider)

    tips = service.retrieve_tips("anything")

    assert tips == []