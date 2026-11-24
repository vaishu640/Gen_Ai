import json
import statistics
from pathlib import Path

LOG = Path("data/ask_log.jsonl")


def load():
    if not LOG.exists():
        raise SystemExit("data/ask_log.jsonl not found. Ask a few questions first.")
    rows = []
    with open(LOG, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except ValueError:
                pass
    return rows


def median(values):
    return round(statistics.median(values)) if values else None


def mean(values):
    return round(statistics.mean(values)) if values else None


def slowest(values):
    if not values:
        return None
    values = sorted(values)
    return values[max(0, min(len(values) - 1, round(0.95 * len(values)) - 1))]


def show(value, unit=""):
    return "-" if value is None else str(value) + unit


rows = load()
if not rows:
    raise SystemExit("The log is empty. Ask a few questions first.")

groups = {"ok": [], "cache_hit": [], "blocked": [], "error": []}
for r in rows:
    groups.setdefault(r.get("status", "ok"), []).append(r)

ok = groups["ok"]
hit = groups["cache_hit"]
total = len(rows)

ok_ms = [r["latency_ms"] for r in ok]
hit_ms = [r["latency_ms"] for r in hit]
prompt_tokens = [r.get("prompt_tokens", 0) for r in ok]
completion_tokens = [r.get("completion_tokens", 0) for r in ok]
total_tokens = [r.get("total_tokens", 0) for r in ok]

avg_total = mean(total_tokens)
saved = avg_total * len(hit) if avg_total is not None else None
speedup = None
if ok_ms and hit_ms:
    speedup = round(median(ok_ms) / max(median(hit_ms), 1))

lines = [
    "| Measure | Value |",
    "|---|---|",
    "| Period | " + rows[0]["time"] + " to " + rows[-1]["time"] + " |",
    "| /ask requests logged | " + str(total) + " |",
    "| Answered by the model | " + str(len(ok)) + " |",
    "| Cache hits | " + str(len(hit)) + " (" + str(round(100 * len(hit) / total)) + "% of requests) |",
    "| Blocked by the input filter | " + str(len(groups["blocked"])) + " |",
    "| Errors | " + str(len(groups["error"])) + " |",
    "| Median latency, model called | " + show(median(ok_ms), " ms") + " |",
    "| Slowest (p95) latency, model called | " + show(slowest(ok_ms), " ms") + " |",
    "| Median latency, cache hit | " + show(median(hit_ms), " ms") + " |",
    "| Cache speed-up | " + ("about " + str(speedup) + "x" if speedup else "-") + " |",
    "| Average prompt tokens per model call | " + show(mean(prompt_tokens)) + " |",
    "| Average completion tokens per model call | " + show(mean(completion_tokens)) + " |",
    "| Average total tokens per model call | " + show(avg_total) + " |",
    "| Total tokens used, all requests | " + str(sum(r.get("total_tokens", 0) for r in rows)) + " |",
    "| Tokens the cache saved (estimate) | " + show(saved) + " |",
]

output = "\n".join(lines) + "\n"
with open("eval/production_notes_table.md", "w", encoding="utf-8") as f:
    f.write(output)

print(output)
print("Saved eval/production_notes_table.md")