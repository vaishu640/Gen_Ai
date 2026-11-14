
import numpy as np
from sentence_transformers import SentenceTransformer
from app.chunking import create_chunks

model = SentenceTransformer("all-MiniLM-L6-v2")


def generate_embeddings(texts):

    return model.encode(
        texts,
        normalize_embeddings=True
    )


def semantic_search(question, chunks, top_k=3):

    if not chunks:
        return []

    texts = [chunk["text"] for chunk in chunks]

    question_vector = generate_embeddings([question])[0]
    text_vectors = generate_embeddings(texts)

    scores = np.dot(text_vectors, question_vector)

    best = np.argsort(scores)[::-1][:top_k]

    results = []

    for index in best:

        results.append({
            **chunks[index],
            "score": float(scores[index])
        })

    return results


if __name__ == "__main__":

    chunks = create_chunks()

    question = "What documents are required for certification?"

    results = semantic_search(question, chunks)

    for result in results:

        print("\nQuestion:", question)
        print("Title:", result["title"])
        print("Source:", result["source"])
        print("Page:", result["page"])
        print("Score:", round(result["score"], 3))
        print("Text:", result["text"][:150])
