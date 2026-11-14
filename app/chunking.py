
from pathlib import Path
from pypdf import PdfReader
from bs4 import BeautifulSoup

RAW_DIR = Path("data/raw")

def split_text(text, size=1000, overlap=150):

    text = " ".join(text.split())
    chunks = []

    start = 0

    while start < len(text):

        chunk = text[start:start + size]

        if chunk.strip():
            chunks.append(chunk)

        start += size - overlap

    return chunks


def create_chunks():

    all_chunks = []

    for file in RAW_DIR.rglob("*"):

        if not file.is_file():
            continue

        title = file.stem
        pages = []

        if file.suffix.lower() == ".pdf":

            pdf = PdfReader(str(file))

            for page_no, page in enumerate(pdf.pages, 1):
                pages.append((page_no, page.extract_text() or ""))

        elif file.suffix.lower() in [".txt", ".md"]:
            pages.append((1, file.read_text(encoding="utf-8")))

        elif file.suffix.lower() in [".html", ".htm"]:

            soup = BeautifulSoup(
                file.read_text(encoding="utf-8"),
                "html.parser"
            )

            title = soup.title.get_text(strip=True) if soup.title else title
            pages.append((1, soup.get_text(separator=" ", strip=True)))

        else:
            continue

        for page_no, text in pages:

            for i, chunk in enumerate(split_text(text)):

                all_chunks.append({
                    "text": chunk,
                    "source": str(file),
                    "page": page_no,
                    "title": title,
                    "id": f"{file.stem}_{page_no}_{i}"
                })

    return all_chunks


if __name__ == "__main__":

    chunks = create_chunks()

    print("Total chunks:", len(chunks))

    for chunk in chunks[:3]:
        print(chunk)
