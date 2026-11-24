| Measure | Value |
|---|---|
| Period | 2026-11-23T11:03:20 to 2026-11-24T09:59:22 |
| /ask requests logged | 57 |
| Answered by the model | 29 |
| Cache hits | 21 (37% of requests) |
| Blocked by the input filter | 7 |
| Errors | 0 |
| Median latency, model called | 798 ms |
| Slowest (p95) latency, model called | 42518 ms |
| Median latency, cache hit | 2 ms |
| Cache speed-up | about 399x |
| Average prompt tokens per model call | 856 |
| Average completion tokens per model call | 83 |
| Average total tokens per model call | 939 |
| Total tokens used, all requests | 27233 |
| Tokens the cache saved (estimate) | 19719 |

## Production notes

Measured from the log my API wrote (`data/ask_log.jsonl`, copy in `docs/ask_log_sample.jsonl`) on my own computer with the Groq free tier and the model `openai/gpt-oss-20b`.

PASTE THE TABLE HERE

- **Latency:** a question that needs the model took a median of [number] ms (slowest [number] ms). Almost all of that time is the model call.
- **Cache:** [number] of [number] requests ([number]%) were answered from the cache in a median of [number] ms, about [number]x faster, and used no tokens.
- **Tokens:** one model call uses about [number] tokens on average ([number] in the prompt, [number] in the answer), which is [number] tokens in total across the whole log.
- **Safety:** [number] request(s) were blocked by the input filter without calling the model, so they cost nothing.

Limits: these numbers come from one computer and a small sample, and the free tier sometimes adds waiting time when it rate-limits.
