# OrganicPath — Interview & Demo Guide

## 60-Second Pitch

"I built **OrganicPath**, a grounded question-answering assistant and workflow agent designed for PGS-India organic farming groups in Kopargaon, Maharashtra. Farmers and group leaders often struggle with dense, multi-edition certification manuals where small misunderstandings—like conversion periods or land-holding limits—can risk an entire group's organic status.

OrganicPath indexes official PGS-India guidelines, operational manuals, and FAQs into ChromaDB using sentence embeddings, and answers queries strictly from retrieved passages with page-level citations. If a rule isn't in the documents, it explicitly says 'I don't know' instead of guessing. Beyond Q&A, I built a LangGraph agent with a conversion-timeline calculator and a human-in-the-loop approval step for peer-appraisal readiness checks. For production readiness, I added an in-memory TTL cache, per-request latency and token logging, input validation, a prompt-injection filter, and a 25-test CI pipeline packaged with Docker Compose."

---

## Hardest Technical Problem (Interview Story)

**The Problem:**
The PGS-India knowledge base contains two parallel certification tracks (**PGS Organic** vs. **PGS Natural Farming**) as well as multiple manual editions (e.g., Revised Guidelines Edition 2 alongside older operational manuals and FAQs). They share nearly identical terminology—such as local group size, annual meeting counts, and conversion timelines—but specify conflicting thresholds. Furthermore, the PGS standards cross-reference national NPOP/NSOP regulations, requiring multi-passage reasoning while preventing the LLM from blending two systems into one inaccurate rule.

**How I Solved It:**
1. **Rich Chunk Metadata:** During ingestion (`app/chunking.py` and `app/vectorstore.py`), I attached explicit `title`, `source`, and `page` metadata to every chunk, and tuned chunk size (`60` vs. `120` words) against a 15-question evaluation suite.
2. **Strict Grounding & Attribution Prompts:** In `prompts/rag_system.md`, I enforced rules requiring bracketed citations (`[1]`, `[2]`) for every claim and explicitly instructing the model to report **both** values and name each source document whenever two editions or systems disagree.
3. **Abstention Guardrails:** For questions not covered in the local manuals (such as crop-specific perennial vs. annual classifications deferred to Regional Councils, or unindexed local market prices), the model is instructed to set `"answerable": false` and refuse to speculate.

---

## 10 Likely Interview Questions & Answers

### 1. Why did you choose RAG instead of fine-tuning a model on PGS-India rules?
Certification guidelines change across editions and require verifiable page-level citations for audits. Fine-tuning bakes static knowledge into weights, makes source attribution unreliable, and risks hallucinating numbers. RAG lets us update documents by re-indexing, inspect the exact retrieved chunks, and enforce strict abstention when evidence is missing.

### 2. How did you prevent hallucinations in high-stakes agricultural compliance rules?
Three ways: (a) a low sampling temperature (`0.2`) and strict JSON output schema separating `"answerable"`, `"answer"`, and `"cited"`; (b) system instructions forbidding outside knowledge and requiring chunk citations for every claim; and (c) testing against unanswerable trap questions in our 15-question eval set.

### 3. How did you evaluate retrieval quality and choose your chunk size?
I built a 15-question benchmark (13 answerable across different documents, 2 unanswerable) and compared `chunk_words=60` against `chunk_words=120`. Smaller 60-word chunks improved precision on specific numeric rules (such as meeting counts and member minimums) without diluting embeddings with unrelated paragraphs.

### 4. What happens when two PGS documents disagree on a rule?
Rather than letting the LLM pick one arbitrarily, the system prompt explicitly instructs it to surface both figures and cite each source document and page number so the farmer group and Regional Council can verify which edition applies.

### 5. Why did you add a LangGraph agent on top of standard RAG?
Some farmer workflows require deterministic state and multi-step actions rather than pure text retrieval—such as calculating exact organic conversion end-dates from a start date (`conversion_timeline`) or flagging non-compliant members before peer appraisal. LangGraph gave me typed state, tool execution, session memory, and a clean human-in-the-loop interrupt before finalizing high-impact group decisions.

### 6. How did you handle latency and API rate limits on the free tier?
I added an `OrderedDict` LRU+TTL in-memory cache (`app/cache.py`, 100 entries, 1-hour TTL) normalized on lower-cased, whitespace-collapsed questions so repeat queries return in milliseconds with zero LLM tokens. For cold calls, `app/llm.py` implements exponential/header-aware retry logic for HTTP `429` rate limits and transient connection drops.

### 7. How do you protect the `/ask` endpoint against prompt injection and abuse?
I implemented defense-in-depth: (1) strict input validation (`MAX_QUESTION_CHARS = 500`, bounded `k`, allowed chunk sizes); (2) a regex pre-filter that blocks common jailbreak/override phrases before hitting the LLM; and (3) prompt separation marking retrieved context and user text strictly as untrusted data. Both direct injection and poisoned-chunk injection are covered by automated tests in `tests/test_production.py`.

### 8. How do your unit tests run without calling live APIs or loading ChromaDB?
In `tests/conftest.py`, I monkeypatched `app.vectorstore` with an in-memory fake module and swapped `ask_llm` with deterministic stub functions. This lets all 25 `pytest` tests run offline in ~6–8 seconds inside GitHub Actions CI.

### 9. What are the main limitations of your current architecture?
First, the cache and LangGraph session checkpointer live in process memory, so they reset on restart and wouldn't share state across multiple workers. Second, the regex injection filter catches known patterns rather than semantic adversarial prompts. Third, the vector index currently relies purely on dense embeddings without hybrid BM25 keyword search for exact section codes.

### 10. What would you build next if deploying this for real farmer groups?
I would move caching and session state to Redis, add hybrid dense + BM25 retrieval with a cross-encoder reranker, support Marathi voice/text translation for accessibility in Maharashtra, and add per-user rate limiting and authentication.