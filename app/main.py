from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.smart_search import SmartSearch, load_records

app = FastAPI(title="OrganicPath API")

records = load_records()
for i, r in enumerate(records):
    r["id"] = i + 1

engine = SmartSearch(records)


class Question(BaseModel):
    question: str


@app.get("/health")
def health():
    return {"status": "ok", "records": len(records)}


@app.get("/records")
def list_records(stage: str = None):
    if stage:
        return [r for r in records if r["stage"] == stage]
    return records


@app.get("/records/{record_id}")
def get_record(record_id: int):
    for r in records:
        if r["id"] == record_id:
            return r
    raise HTTPException(status_code=404, detail="Record not found")


@app.get("/search")
def search(q: str):
    return engine.search(q)


@app.post("/questions")
def ask(body: Question):
    results = engine.search(body.question, top_k=3)
    if len(results) == 0 or results[0]["score"] < 0.1:
        return {
            "answer": "I could not find this in the PGS-India documents I have.",
            "sources": [],
        }
    best = results[0]
    return {
        "answer": best["rule"],
        "from": best["source_doc"],
        "sources": [{"id": r["id"], "topic": r["topic"], "source_doc": r["source_doc"],
                     "source_url": r["source_url"]} for r in results],
    }