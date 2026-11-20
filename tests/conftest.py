import os
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)  # the app reads data/ and prompts/ with relative paths
sys.path.insert(0, str(ROOT))

FAKE_HITS = [
    {
        "id": "guidelines-p23-c1",
        "distance": 0.31,
        "title": "PGS-India Revised Guidelines, Edition 2 (2023)",
        "page": 23,
        "source": "pgs_guidelines_2023.pdf",
        "source_url": "https://example.org/guidelines.pdf",
        "text": "A Local group should comprise of minimum 5 members belonging to the "
        "same village or close by villages.",
    },
    {
        "id": "faq-p1-c4",
        "distance": 0.42,
        "title": "PGS-India FAQ page",
        "page": 1,
        "source": "pgs_faqs.html",
        "source_url": "https://example.org/faqs",
        "text": "To make a local group, organize at least 5 members living in the "
        "same or close by villages.",
    },
]


def fake_semantic_search(query, k=5, words=120):
    return FAKE_HITS[:k]


def fake_collection_size(words=120):
    return len(FAKE_HITS)


# Replace the real vector store (Chroma + embedding model) with a tiny fake,
# so the tests need no internet and no database.
fake_vectorstore = types.ModuleType("app.vectorstore")
fake_vectorstore.DEFAULT_WORDS = 120
fake_vectorstore.semantic_search = fake_semantic_search
fake_vectorstore.collection_size = fake_collection_size
sys.modules["app.vectorstore"] = fake_vectorstore