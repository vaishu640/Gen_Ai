import json
import time
from app.rag import answer_question, normalize
from app.llm import LLMError
from app.vectorstore import collection_size

CONFIGS = [
    {"name": "A", "chunk_words": 120, "k": 3},
    {"name": "B", "chunk_words": 60, "k": 5},
]
PAUSE = 5          # seconds between calls (free tier rate limit)


def has_any(text, terms):
    text = normalize(text)
    return any(normalize(t) in text for t in terms)


def ask_with_retry(question, k, words):
    for attempt in range(4):
        try:
            return answer_question(question, k, words)
        except LLMError as error:
            if "429" in str(error) and attempt < 3:
                print("   rate limit, waiting 25 seconds ...")
                time.sleep(25)
            else:
                raise


def evaluate(config, rows):
    words, k = config["chunk_words"], config["k"]
    details = []
    for row in rows:
        try:
            result = ask_with_retry(row["question"], k, words)
        except Exception as error:
            result = {"answer": "ERROR: " + str(error), "answerable": False,
                      "retrieved": [], "citations": [], "best_distance": None}
        time.sleep(PAUSE)

        retrieved_text = " ".join(h["text"] for h in result["retrieved"])
        if row["answerable"]:
            retrieval_hit = has_any(retrieved_text, row["gold_terms"])
            correct = (result["answerable"]
                       and has_any(result["answer"], row["answer_terms"]))
        else:
            retrieval_hit = None
            correct = not result["answerable"]      # correct = it refused

        details.append({"row": row, "result": result,
                        "retrieval_hit": retrieval_hit, "correct": correct})
        print("  row", row["id"], "->", "OK" if correct else "WRONG")
    return details


def summarize(details):
    answerable = [d for d in details if d["row"]["answerable"]]
    refusals = [d for d in details if not d["row"]["answerable"]]
    hit = sum(1 for d in answerable if d["retrieval_hit"])
    good = sum(1 for d in answerable if d["correct"])
    refused = sum(1 for d in refusals if d["correct"])

    def avg(items):
        values = [d["result"]["best_distance"] for d in items
                  if d["result"].get("best_distance") is not None]
        return sum(values) / len(values) if values else None

    return {
        "retrieval": hit, "n_answerable": len(answerable),
        "answered": good, "refused": refused, "n_refusals": len(refusals),
        "overall": good + refused, "total": len(details),
        "dist_answerable": avg(answerable), "dist_unanswerable": avg(refusals),
    }


def fmt(value):
    return "-" if value is None else format(value, ".3f")


def main():
    with open("eval/eval_set.json", encoding="utf-8") as f:
        rows = json.load(f)

    for config in CONFIGS:
        if collection_size(config["chunk_words"]) == 0:
            print("Index for", config["chunk_words"],
                  "words is empty. Run: python -m app.vectorstore")
            return

    summaries = {}
    all_details = {}
    for config in CONFIGS:
        print("Config", config["name"], "-", config["chunk_words"],
              "words, top", config["k"])
        details = evaluate(config, rows)
        all_details[config["name"]] = details
        summaries[config["name"]] = summarize(details)

    def key(config):
        s = summaries[config["name"]]
        return (s["overall"], s["retrieval"], -config["k"])
    winner = max(CONFIGS, key=key)

    table = [
        "| Config | Chunk size | Top-k | Retrieval hit | Correct answers | Correct 'I don't know' | Overall |",
        "|--------|-----------|-------|---------------|-----------------|------------------------|---------|",
    ]
    for config in CONFIGS:
        s = summaries[config["name"]]
        label = config["name"] + (" (winner)" if config is winner else "")
        table.append("| " + label + " | " + str(config["chunk_words"]) + " words | "
                     + str(config["k"]) + " | " + str(s["retrieval"]) + "/" + str(s["n_answerable"])
                     + " | " + str(s["answered"]) + "/" + str(s["n_answerable"])
                     + " | " + str(s["refused"]) + "/" + str(s["n_refusals"])
                     + " | " + str(s["overall"]) + "/" + str(s["total"]) + " |")

    with open("eval/winner_table.md", "w", encoding="utf-8") as f:
        f.write("\n".join(table) + "\n")

    lines = ["# RAG evaluation results", "",
             "15 questions (13 answerable, 2 that my documents cannot answer).", ""]
    lines += table
    lines += ["", "Average distance of the closest chunk (smaller = closer):", ""]
    for config in CONFIGS:
        s = summaries[config["name"]]
        lines.append("- Config " + config["name"] + ": answerable questions "
                     + fmt(s["dist_answerable"]) + ", unanswerable questions "
                     + fmt(s["dist_unanswerable"]))
    lines.append("")

    for config in CONFIGS:
        lines += ["## Config " + config["name"] + " (" + str(config["chunk_words"])
                  + " words, top-" + str(config["k"]) + ")", "",
                  "| id | question | answerable | retrieval hit | correct | distance | answer |",
                  "|----|----------|-----------|---------------|---------|----------|--------|"]
        for d in all_details[config["name"]]:
            q = d["row"]["question"][:60]
            answer = str(d["result"]["answer"]).replace("|", "/").replace("\n", " ")[:160]
            hit = "-" if d["retrieval_hit"] is None else ("yes" if d["retrieval_hit"] else "no")
            lines.append("| " + str(d["row"]["id"]) + " | " + q + " | "
                         + str(d["row"]["answerable"]) + " | " + hit + " | "
                         + ("yes" if d["correct"] else "NO") + " | "
                         + fmt(d["result"].get("best_distance")) + " | " + answer + " |")
        lines.append("")

    with open("eval/eval_results.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print("\nWinner: config", winner["name"])
    print("\n".join(table))
    print("\nSaved eval/eval_results.md and eval/winner_table.md")


if __name__ == "__main__":
    main()