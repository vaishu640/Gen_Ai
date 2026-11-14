from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.smart_search import SmartSearch, load_records
from app.llm import ask_llm, parse_json_reply, LLMError

app = FastAPI(title="OrganicPath API")

records = load_records()
for i, r in enumerate(records):
    r["id"] = i + 1

engine = SmartSearch(records)


class Question(BaseModel):
    question: str


class ChatRequest(BaseModel):
    question: str
    prompt_version: str = "v2"


def load_prompt(name):
    with open("prompts/" + name + ".md", encoding="utf-8") as f:
        return f.read()


def build_context(found):
    if len(found) == 0:
        return "(no matching records found)"
    lines = []
    for r in found:
        lines.append("[" + str(r["id"]) + "] " + r["topic"]
                     + " | source: " + r["source_doc"]
                     + " | rule: " + r["rule"])
    return "\n".join(lines)


@app.get("/health")
def health():
    return {"status": "ok", "records": len(records)}


@app.get("/records")
def list_records():
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
    results = engine.search(body.question)
    if len(results) == 0 or results[0]["score"] < 0.1:
        return {"answer": "I could not find this in the PGS-India documents I have.",
                "sources": []}
    best = results[0]
    return {
        "answer": best["rule"],
        "from": best["source_doc"],
        "sources": [{"id": r["id"], "topic": r["topic"],
                     "source_doc": r["source_doc"],
                     "source_url": r["source_url"]} for r in results],
    }


@app.post("/chat")
def chat(body: ChatRequest):
    if body.prompt_version not in ("v1", "v2"):
        raise HTTPException(status_code=400, detail="prompt_version must be v1 or v2")

    found = engine.search(body.question, top_k=3)
    system = load_prompt("system")
    task = load_prompt("task_" + body.prompt_version)
    user = (task.replace("{context}", build_context(found))
                .replace("{question}", body.question))

    try:
        reply = ask_llm(system, user)
    except LLMError as error:
        raise HTTPException(status_code=502, detail=str(error))

    result = parse_json_reply(reply)
    result["prompt_version"] = body.prompt_version
    result["sources"] = [{"id": r["id"], "topic": r["topic"],
                          "source_doc": r["source_doc"],
                          "source_url": r["source_url"]} for r in found]
    return result