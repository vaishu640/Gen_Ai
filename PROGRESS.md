# OrganicPath — Capstone Progress Tracker

- [x] **Day 1:** Repository setup, folder structure, FastAPI skeleton (`/health`), and environment configuration
- [x] **Day 2:** Document ingestion (`app/ingest.py`), PDF text extraction, and metadata tagging for PGS-India guidelines
- [x] **Day 3:** Text chunking (`app/chunking.py`) and embedding pipeline (`app/embed.py`) with ChromaDB (`app/vectorstore.py`)
- [x] **Day 4:** Grounded Q&A endpoint (`/ask`), strict JSON response schema, and citation enforcement (`prompts/rag_system.md`)
- [x] **Day 5:** Abstention guardrails (`"I don't know"` fallback) and cross-document conflict attribution (PGS Organic vs. PGS Natural Farming)
- [x] **Day 6:** 15-question evaluation suite (`eval/`) and chunk-size tuning (`60` vs. `120` words)
- [x] **Day 7:** Streamlit user interface (`ui/app.py`) with interactive Q&A and citation display
- [x] **Day 8:** LangGraph agent (`app/agent.py`) with stateful conversation memory and deterministic tools (`conversion_timeline`, readiness check)
- [x] **Day 9:** Human-in-the-loop (HITL) interrupt & approval flow for peer-appraisal readiness checks
- [x] **Day 10:** Production caching (`app/cache.py` LRU+TTL), retry logic (`app/llm.py`), and JSONL request telemetry (`data/ask_log.jsonl`)
- [x] **Day 11:** Input validation, regex prompt-injection filter, and security test suite (`tests/test_production.py`)
- [x] **Day 12:** Docker & Docker Compose packaging (`Dockerfile`, `docker-compose.yml`) and GitHub Actions CI (`ruff` + 25 `pytest` tests + Docker build)
- [x] **Day 13:** Production latency/cost benchmarking (`eval/production_numbers.md`), `README.md` with Mermaid architecture diagram, and `docs/resume.md`
- [x] **Day 14:** Interview & demo guide (`docs/interview.md`), demo rehearsal, final checklist closure, and `final` release tag

---

## Final Completion Summary

- **CI & Testing:** Passing GitHub Actions workflow (`ruff` lint check, 25 offline `pytest` unit/integration tests, and Docker image build).
- **Production Safeguards:** In-memory LRU+TTL cache, per-request latency/token logging (`data/ask_log.jsonl`), strict input length/parameter validation, and prompt-injection defenses.
- **Documentation:** Complete `README.md` with Mermaid architecture diagram and real benchmark numbers, `docs/resume.md`, and `docs/interview.md`.