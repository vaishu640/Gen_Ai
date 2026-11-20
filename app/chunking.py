import json
import re

from bs4 import BeautifulSoup
from pypdf import PdfReader

RAW = "data/raw/"
CHUNK_WORDS = 120

DOCS = {
    "pgs_faqs.html": {
        "title": "PGS-India FAQ page",
        "url": "https://pgsindia-ncof.gov.in/faqs",
    },
    "pgs_guidelines_2023.pdf": {
        "title": "PGS-India Revised Guidelines, Edition 2 (2023)",
        "url": "https://pgsindia-ncof.gov.in/uploads/operational_manuals/165217720544Revised_PGS_India_Guidlines.pdf",
    },
    "pgs_standards.pdf": {
        "title": "PGS-India Standards",
        "url": "https://hpssopca.hp.gov.in/wp-content/uploads/2023/07/PGS_India_Standards.pdf",
    },
}


def clean(text):
    return re.sub(r"\s+", " ", text).strip()


def read_pages(filename):
    path = RAW + filename
    pages = []
    if filename.endswith(".pdf"):
        reader = PdfReader(path)
        for number, page in enumerate(reader.pages, 1):
            try:
                text = page.extract_text() or ""
            except Exception:
                text = ""
            pages.append((number, clean(text)))
    else:
        with open(path, encoding="utf-8", errors="ignore") as f:
            soup = BeautifulSoup(f.read(), "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        pages.append((1, clean(soup.get_text(" "))))
    return pages


def split_words(text, chunk_words, overlap_words):
    words = text.split()
    step = max(chunk_words - overlap_words, 1)
    pieces = []
    for start in range(0, len(words), step):
        piece = " ".join(words[start:start + chunk_words])
        if len(piece) > 60:
            pieces.append(piece)
        if start + chunk_words >= len(words):
            break
    return pieces


def make_chunks(chunk_words=CHUNK_WORDS, overlap_words=None):
    if overlap_words is None:
        overlap_words = chunk_words // 6
    chunks = []
    for filename, info in DOCS.items():
        try:
            pages = read_pages(filename)
        except FileNotFoundError:
            print("Missing file, skipped:", filename)
            continue
        stem = filename.rsplit(".", 1)[0]
        for page_number, text in pages:
            for n, piece in enumerate(split_words(text, chunk_words, overlap_words), 1):
                chunks.append({
                    "id": stem + "-p" + str(page_number) + "-c" + str(n),
                    "text": piece,
                    "source": filename,
                    "source_url": info["url"],
                    "page": page_number,
                    "title": info["title"],
                })
    return chunks


# the old name from Day 7, so older files keep working
create_chunks = make_chunks


if __name__ == "__main__":
    chunks = make_chunks()
    with open("data/chunks.json", "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)
    print("Total chunks:", len(chunks))