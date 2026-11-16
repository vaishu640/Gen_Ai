import json
import re
from app.vectorstore import semantic_search, DEFAULT_WORDS
from app.llm import ask_llm

IDK = "I don't know. This is not in the PGS-India documents I have."

# If the closest chunk is farther than this number, answer "I don't know"
# without asking the model. None = off.
MAX_DISTANCE = None


def load_prompt(name):
    with open("prompts/" + name + ".md", encoding="utf-8") as f:
        return f.read()


def normalize(text):
    return str(text).replace("\u2019", "'").replace("\u2011", "-").lower()


def build_context(hits):
    lines = []
    for n, h in enumerate(hits, 1):
        lines.append("[" + str(n) + "] " + h["title"] + " (page "
                     + str(h["page"]) + "): " + h["text"])
    return "\n\n".join(lines)


def parse_reply(text):
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        return json.loads(text[start:end + 1])
    except ValueError:
        return None


def unknown_result(question, hits, k, words, note):
    return {
        "question": question,
        "answer": IDK,
        "answerable": False,
        "confidence": "low",
        "citations": [],
        "retrieved": hits,
        "best_distance": hits[0]["distance"] if hits else None,
        "config": {"chunk_words": words, "top_k": k},
        "note": note,
    }


def answer_question(question, k=3, words=DEFAULT_WORDS):
    hits = semantic_search(question, k, words)

    if not hits:
        return unknown_result(question, hits, k, words, "no chunks found")
    if MAX_DISTANCE is not None and hits[0]["distance"] > MAX_DISTANCE:
        return unknown_result(question, hits, k, words, "closest chunk is too far away")

    system = load_prompt("rag_system")
    task = load_prompt("rag_task")
    user = (task.replace("{context}", build_context(hits))
                .replace("{question}", question))
    reply = ask_llm(system, user)

    data = parse_reply(reply)
    json_ok = data is not None
    if data is None:
        data = {"answer": reply.strip(), "answerable": True, "confidence": "low"}

    answer = str(data.get("answer") or "").strip()
    answerable = str(data.get("answerable")).lower() == "true"
    if "don't know" in normalize(answer) or answer == "":
        answerable = False
    if not answerable:
        return unknown_result(question, hits, k, words, "model said it cannot answer")

    numbers = set()
    for n in data.get("cited") or []:
        try:
            numbers.add(int(n))
        except (TypeError, ValueError):
            pass
    for n in re.findall(r"\[(\d+)\]", answer):
        numbers.add(int(n))
    numbers = sorted(n for n in numbers if 1 <= n <= len(hits))

    note = ""
    if not numbers:
        numbers = [1]
        note = "model gave no citation, showing the top retrieved chunk"

    citations = []
    for n in numbers:
        h = hits[n - 1]
        citations.append({
            "n": n,
            "title": h["title"],
            "page": h["page"],
            "source_url": h["source_url"],
            "snippet": h["text"][:300],
        })

    confidence = str(data.get("confidence") or "low").lower()
    if confidence not in ("high", "medium", "low"):
        confidence = "low"

    return {
        "question": question,
        "answer": answer,
        "answerable": True,
        "confidence": confidence,
        "citations": citations,
        "retrieved": hits,
        "best_distance": hits[0]["distance"],
        "config": {"chunk_words": words, "top_k": k},
        "json_ok": json_ok,
        "note": note,
    }