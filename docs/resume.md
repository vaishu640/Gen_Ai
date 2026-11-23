# OrganicPath: resume notes

## One line
OrganicPath is a question-answering assistant that helps a PGS-India organic-farming group in Kopargaon check certification rules, grounded in official documents, with page-level citations.

## Resume bullets (choose 3 or 4)
- Built a retrieval-augmented assistant (FastAPI, Chroma, sentence embeddings, Groq LLM) over 3 official PGS-India sources (2 PDFs and an FAQ page), indexing 891 60-word chunks (and 470 120-word chunks) with source, page and title for every answer.
- Designed a 15-question evaluation set (13 answerable, 2 unanswerable) and used it to compare two retrieval settings; the best setting scored 15/15, including correct "I don't know" answers.
- Added production safeguards: per-request latency and token logging (median 748 ms per question, 946 average tokens), an in-memory cache (374x faster on repeats at 2 ms), an input limit and a prompt-injection filter with tests.
- Wrote 25 automated pytest tests with a fake LLM, linted the code with ruff, and containerised the API and the Streamlit UI with Docker Compose.
- Built an agent with a date tool (`conversion_timeline`), memory and a human approval step using LangGraph, and a peer-appraisal readiness checklist that flags farmers whose non-compliance could put the group at risk.

## Tech
Python, FastAPI, Streamlit, ChromaDB, sentence-transformers, Groq API, LangGraph, pandas, scikit-learn, pytest, ruff, Docker.

## Honest limits (good to say in an interview)
- The two source documents disagree on some numbers (for example land limit, meetings), so every answer names its document.
- The conversion period comes from the PGS-India Standards, but whether a crop such as sugarcane is annual or perennial is not stated there, so the bot tells the user to ask the Regional Council.
- The injection filter is simple and the cache and agent memory live in server memory.

## 30-second answer
"I built OrganicPath for a farmer group that wants PGS-India organic certification. It finds the right passages in the official documents and answers only from them, with the page it came from. If the documents do not contain the answer, it says so. I tested it on 15 questions, added a cache and input checks, and measured latency and token use per request."