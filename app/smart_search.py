import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

SYNONYMS = {
    "farmer": "member",
    "farmers": "members",
    "needed": "minimum",
    "need": "minimum",
    "required": "minimum",
    "many": "minimum size number",
}


def load_records():
    with open("data/records.json", encoding="utf-8") as f:
        return json.load(f)


def expand(query):
    words = query.lower().replace("?", "").split()
    extra = [SYNONYMS[w] for w in words if w in SYNONYMS]
    return query + " " + " ".join(extra)


class SmartSearch:
    def __init__(self, records):
        self.records = records
        texts = [(r["topic"] + " ") * 2 + r["rule"] for r in records]
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.matrix = self.vectorizer.fit_transform(texts)

    def search(self, query, top_k=3):
        query_vector = self.vectorizer.transform([expand(query)])
        scores = cosine_similarity(query_vector, self.matrix)[0]
        best = scores.argsort()[::-1][:top_k]
        results = []
        for i in best:
            if scores[i] > 0:
                item = dict(self.records[i])
                item["score"] = round(float(scores[i]), 3)
                results.append(item)
        return results