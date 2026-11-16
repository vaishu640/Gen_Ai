
import chromadb

from app.chunking import create_chunks
from app.embed import generate_embeddings

# ChromaDB database path
CHROMA_PATH = "data/chroma_db"

# Default chunk size
DEFAULT_WORDS = 120

# Chunk sizes for comparison
SIZES = [60, 120]

# Create persistent ChromaDB client
client = chromadb.PersistentClient(path=CHROMA_PATH)


def collection_name(words):
    return f"organicpath_w{words}"


def get_collection(words=DEFAULT_WORDS):
    return client.get_or_create_collection(
        name=collection_name(words),
        metadata={"hnsw:space": "cosine"}
    )


def embed(texts, batch=64):
    vectors = []

    for start in range(0, len(texts), batch):
        part = generate_embeddings(texts[start:start + batch])

        if hasattr(part, "tolist"):
            part = part.tolist()

        vectors.extend(part)

    return vectors


def index_all(words=DEFAULT_WORDS):

    collection = get_collection(words)

    chunks = create_chunks(chunk_words=words)

    if not chunks:
        print("No document chunks found.")
        return 0

    batch = 100

    for start in range(0, len(chunks), batch):

        part = chunks[start:start + batch]

        texts = [chunk["text"] for chunk in part]

        collection.upsert(
            ids=[chunk["id"] for chunk in part],
            documents=texts,
            embeddings=embed(texts),
            metadatas=[
                {
                    "source": chunk["source"],
                    "source_url": chunk.get("source_url", ""),
                    "page": chunk["page"],
                    "title": chunk["title"]
                }
                for chunk in part
            ]
        )

        print(
            "Indexed",
            min(start + batch, len(chunks)),
            "of",
            len(chunks)
        )

    return collection.count()


def collection_size(words=DEFAULT_WORDS):
    return get_collection(words).count()


def semantic_search(query, k=5, words=DEFAULT_WORDS):

    collection = get_collection(words)

    if collection.count() == 0:
        return []

    results = collection.query(
        query_embeddings=embed([query]),
        n_results=min(k, collection.count())
    )

    hits = []

    for i in range(len(results["ids"][0])):

        metadata = results["metadatas"][0][i]

        hits.append({
            "id": results["ids"][0][i],
            "distance": round(
                float(results["distances"][0][i]), 4
            ),
            "title": metadata["title"],
            "page": metadata["page"],
            "source": metadata["source"],
            "source_url": metadata.get("source_url", ""),
            "text": results["documents"][0][i]
        })

    return hits


def search_documents(query, top_k=3):
    return semantic_search(query, top_k)


if __name__ == "__main__":

    for size in SIZES:

        print("Indexing chunk size", size, "words...")

        total = index_all(size)

        print(
            "Collection",
            collection_name(size),
            "now holds",
            total,
            "chunks"
        )

    print("\nTest search:")

    for hit in semantic_search(
        "How many farmers are needed to form a group?",
        3
    ):
        print(hit["distance"], "|", hit["title"], "| page", hit["page"])
