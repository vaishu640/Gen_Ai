import hashlib
import os
import re

import numpy as np

from app.chunking import create_chunks

_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def _light_embed(texts, dim=384):
    vectors = np.zeros((len(texts), dim), dtype=np.float32)
    for i, text in enumerate(texts):
        for token in re.findall(r"\w+", text.lower()):
            idx = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16) % dim
            vectors[i, idx] += 1.0
        norm = np.linalg.norm(vectors[i])
        if norm > 0:
            vectors[i] /= norm
    return vectors


def generate_embeddings(texts):
    if os.getenv("LIGHT_EMBED") == "1":
        return _light_embed(texts)
    return _get_model().encode(texts, normalize_embeddings=True)


def semantic_search(question, chunks, top_k=3):
    if not chunks:
        return []

    texts = [chunk["text"] for chunk in chunks]
    question_vector = generate_embeddings([question])[0]
    text_vectors = generate_embeddings(texts)

    scores = np.dot(text_vectors, question_vector)
    best = np.argsort(scores)[::-1][:top_k]

    return [{**chunks[index], "score": float(scores[index])} for index in best]


if __name__ == "__main__":
    chunks = create_chunks()
    question = "What documents are required for certification?"
    for result in semantic_search(question, chunks):
        print("\nQuestion:", question)
        print("Title:", result["title"])
        print("Source:", result["source"])
        print("Page:", result["page"])
        print("Score:", round(result["score"], 3))
        print("Text:", result["text"][:150])