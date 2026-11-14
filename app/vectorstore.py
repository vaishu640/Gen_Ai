
import chromadb

from app.chunking import create_chunks
from app.embed import generate_embeddings

# Create persistent ChromaDB database
client = chromadb.PersistentClient(path="data/chroma_db")

# Create or get collection
collection = client.get_or_create_collection(
    name="organicpath"
)


def index_documents():

    # Get chunks from chunking.py
    chunks = create_chunks()

    if not chunks:
        print("No document chunks found.")
        return

    texts = [chunk["text"] for chunk in chunks]

    # Generate embeddings
    embeddings = generate_embeddings(texts)

    # Store chunks in ChromaDB
    collection.upsert(
        ids=[chunk["id"] for chunk in chunks],
        documents=texts,
        embeddings=embeddings.tolist(),
        metadatas=[
            {
                "source": chunk["source"],
                "page": chunk["page"],
                "title": chunk["title"]
            }
            for chunk in chunks
        ]
    )

    print("Total indexed chunks:", collection.count())


def search_documents(query, top_k=3):

    if collection.count() == 0:
        return []

    query_embedding = generate_embeddings([query])

    results = collection.query(
        query_embeddings=query_embedding.tolist(),
        n_results=min(top_k, collection.count())
    )

    output = []

    for i in range(len(results["ids"][0])):

        output.append({
            "text": results["documents"][0][i],
            "source": results["metadatas"][0][i]["source"],
            "page": results["metadatas"][0][i]["page"],
            "title": results["metadatas"][0][i]["title"]
        })

    return output


if __name__ == "__main__":
    index_documents()
