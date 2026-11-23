import json
import logging
import re
import time
from datetime import datetime
from pathlib import Path

from app import cache
from app.llm import LLMError, get_usage, reset_usage
from app.rag import answer_question
from app.vectorstore import collection_size

LOG_FILE = Path(__file__).resolve().parent.parent / "data" / "ask_log.jsonl"

MAX_QUESTION_CHARS = 500
MAX_K = 10
ALLOWED_CHUNK_WORDS = (60, 120)

INJECTION_REFUSAL = ("I can only answer questions about PGS-India certification from the "
                     "official documents. I can't follow instructions that change how I work.")

# Simple patterns for the most common prompt-injection phrases.
INJECTION_PATTERNS = [
    r"ignore (all |any |the )*(previous|prior|above|earlier|your) (instructions|rules|prompts?)",
    r"disregard (all |any |the )*(previous|prior|above|earlier|your) (instructions|rules|prompts?)",
    r"forget (all |any |the )*(previous|prior|above|earlier|your) (instructions|rules|prompts?)",
    r"(reveal|show|print|repeat|display|tell me) (me )?(your|the) (system|hidden|initial|original) (prompt|instructions|rules)",
    r"\byou are now (a|an|the)\b",
    r"\b(jailbreak|developer mode|dan mode)\b",
]

logger = logging.getLogger("organicpath")
if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
    logger.addHandler(_handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False


class InputError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.status_code = status_code


def looks_like_injection(text):
    lowered = text.lower()
    return any(re.search(pattern, lowered) for pattern in INJECTION_PATTERNS)


def check_input(question, k, chunk_words):
    question = " ".join(str(question).split())          # trim and collapse spaces
    if not question:
        raise InputError("The question is empty.")
    if len(question) > MAX_QUESTION_CHARS:
        raise InputError("The question is too long. The limit is "
                         + str(MAX_QUESTION_CHARS) + " characters.")
    if not 1 <= k <= MAX_K:
        raise InputError("k must be between 1 and " + str(MAX_K) + ".")
    if chunk_words not in ALLOWED_CHUNK_WORDS:
        raise InputError("chunk_words must be 60 or 120.")
    return question


def compact(result):
    result = dict(result)
    result["retrieved"] = [{"title": h["title"], "page": h["page"],
                            "distance": h["distance"]}
                           for h in result.get("retrieved", [])]
    return result


def refusal(question, k, chunk_words):
    return {
        "question": question,
        "answer": INJECTION_REFUSAL,
        "answerable": False,
        "confidence": "low",
        "citations": [],
        "retrieved": [],
        "best_distance": None,
        "config": {"chunk_words": chunk_words, "top_k": k},
        "note": "blocked by the input filter",
    }


def write_log(question, status, latency_ms, tokens):
    record = {"time": datetime.now().isoformat(timespec="seconds"),
              "question": question[:120], "status": status,
              "latency_ms": latency_ms}
    record.update(tokens)
    logger.info("ask status=%s latency_ms=%s total_tokens=%s",
                status, latency_ms, tokens["total_tokens"])
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        pass


def handle_ask(question, k=3, chunk_words=120):
    started = time.perf_counter()
    reset_usage()

    question = check_input(question, k, chunk_words)
    if collection_size(chunk_words) == 0:
        raise InputError("The index is empty. Stop the server and run: "
                         "python -m app.vectorstore", 503)

    status = "ok"
    if looks_like_injection(question):
        response = refusal(question, k, chunk_words)
        status = "blocked"
    else:
        key = cache.make_key(question, k, chunk_words)
        response = cache.get(key)
        if response is not None:
            status = "cache_hit"
        else:
            try:
                response = compact(answer_question(question, k, chunk_words))
            except LLMError:
                latency_ms = round((time.perf_counter() - started) * 1000)
                write_log(question, "error", latency_ms, get_usage())
                raise
            cache.put(key, response)

    latency_ms = round((time.perf_counter() - started) * 1000)
    tokens = get_usage()
    write_log(question, status, latency_ms, tokens)
    response["meta"] = {"status": status, "cached": status == "cache_hit",
                        "latency_ms": latency_ms, "tokens": tokens}
    return response