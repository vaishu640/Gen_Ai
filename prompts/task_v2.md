CONTEXT (official PGS-India rule records, each with its source):
{context}

QUESTION: {question}

Follow these steps:
1. Find the records that directly answer the question. Ignore records that only share a few words with it.
2. If no record answers it, set "answer" to "I could not find this in the PGS-India documents I have.", set "confidence" to "low", and suggest asking the Regional Council.
3. Otherwise write the answer in 1 to 3 short sentences and name the source document inside the answer.
4. If records disagree (for example the FAQ page and the 2023 Guidelines), give both values and name each source.
5. Set "confidence" to "high" if one record states the answer directly, "medium" if you combined records or the answer is only partial, and "low" if the context does not answer the question.
6. Set "follow_up" to ONE short question the farmer might ask next, or "" if there is none.

Reply with ONLY this JSON, with no extra text:
{"answer": "...", "confidence": "high|medium|low", "follow_up": "..."}