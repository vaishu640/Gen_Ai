# OrganicPath

Trace organic produce from farm to table.

## Problem
Buyers cannot easily check if produce is really organic.

## Users
Farmers, shop owners and consumers.

## Features
- Store organic product records
- Search by product or farm
- Filter by category

## Tech
Python and JSON

## Author
Vaishnavi

## RAG evaluation (Day 8)

My bot answers only from retrieved chunks of the official PGS-India documents
and cites the source and page. If the chunks do not contain the answer, it
says "I don't know". I tested 2 retrieval settings on 15 questions
(13 answerable, 2 that my documents cannot answer, such as the Pune shop
question).

| Config | Chunk size | Top-k | Retrieval hit | Correct answers | Correct 'I don't know' | Overall |
|--------|-----------|-------|---------------|-----------------|------------------------|---------|
| A | 120 words | 3 | 12/13 | 12/13 | 2/2 | 14/15 |
| B (winner) | 60 words | 5 | 13/13 | 13/13 | 2/2 | 15/15 |


**Winner: config B.** Write 2 sentences in your own words: what B did better
than A (for example smaller chunks and more results), and what the table shows.

Full results: [eval/eval_results.md](eval/eval_results.md)
