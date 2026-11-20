import chromadb
import numpy as np

from app.embed import generate_embeddings

QUESTIONS = [
    ("How many farmers are needed to form a PGS-India local group?", ["5 members", "minimum 5", "at least 5"]),
    ("What is the difference between PGS-Green and PGS-Organic certificates?", ["pgs-green", "pgs green"]),
    ("Can one farmer's mistake cancel organic status for the whole village?", ["entire village", "whole village", "large area"]),
    ("Our 12-member group in Kopargaon joins in December 2026 and grows sugarcane and vegetables. When can we first sell as PGS-Organic, and what documents do we keep till then?", ["conversion", "pgs-green", "registration"]),
    ("Compare PGS-India organic certification with the new Natural Farming Certification. Which suits a group using jeevamrut?", ["natural farming"]),
    ("Which shop in Pune pays the highest price for PGS-certified jaggery?", []),
    ("Can one member of our group own most of the group's land?", ["one third", "land holding", "50%"]),
    ("Can I use chemical fertilizer on one plot and keep my other plots organic?", ["chemical", "parallel production", "part conversion"]),
    ("How many group meetings must we hold each year and how many must each member attend?", ["meeting"]),
    ("Can I export my PGS-certified produce as organic?", ["export"]),
]

client = chromadb.PersistentClient(path="data/chroma_db")
names = [getattr(c, "name", c) for c in client.list_collections()]
if "organicpath_w120" in names:
    collection = client.get_collection("organicpath_w120")
elif "organicpath" in names:
    collection = client.get_collection("organicpath")
else:
    raise SystemExit("No collection found. Run: python -m app.vectorstore")

lines = ["# Semantic search results for my 10 questions", "",
         "Score = how close the chunk is to the question (1.0 = same meaning, higher is better).",
         "Relevant = yes if the chunk really helps answer the question.", ""]

for number, (question, words) in enumerate(QUESTIONS, 1):
    q = np.asarray(generate_embeddings([question]), dtype="float32")[0]
    result = collection.query(query_embeddings=[q.tolist()], n_results=3,
                              include=["documents", "metadatas", "embeddings"])

    lines.append("### Q" + str(number) + ". " + question)
    lines.append("")
    lines.append("| rank | source | page | score | relevant | text |")
    lines.append("|------|--------|------|-------|----------|------|")

    for i in range(len(result["ids"][0])):
        meta = result["metadatas"][0][i]
        text = result["documents"][0][i]
        v = np.asarray(result["embeddings"][0][i], dtype="float32")
        score = float(q @ v / (np.linalg.norm(q) * np.linalg.norm(v) + 1e-9))
        relevant = "yes" if any(w in text.lower() for w in words) else "no"
        short = text[:150].replace("|", "/").replace("\n", " ")
        lines.append("| " + str(i + 1) + " | " + str(meta.get("title") or meta.get("source"))
                     + " | " + str(meta.get("page")) + " | " + format(score, ".3f")
                     + " | " + relevant + " | " + short + " |")
    lines.append("")
    print("done question", number)

lines += ["## My notes", "", "(write 3 or 4 sentences here)", ""]

with open("eval/search_results.md", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("Saved eval/search_results.md")