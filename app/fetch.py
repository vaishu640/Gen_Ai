import os
import requests

SOURCES = {
    "pgs_faqs.html": "https://pgsindia-ncof.gov.in/faqs",
    "pgs_guidelines_2023.pdf": "https://pgsindia-ncof.gov.in/uploads/operational_manuals/165217720544Revised_PGS_India_Guidlines.pdf",
    "pgs_standards.pdf": "https://hpssopca.hp.gov.in/wp-content/uploads/2023/07/PGS_India_Standards.pdf",
    "pgs_documents.html": "https://www.pgsindia-ncof.gov.in/viewdocuments",
}

HEADERS = {"User-Agent": "Mozilla/5.0 (OrganicPath student project)"}


def main():
    os.makedirs("data/raw", exist_ok=True)

    for filename, url in SOURCES.items():
        try:
            response = requests.get(url, headers=HEADERS, timeout=20)
            response.raise_for_status()
        except requests.exceptions.RequestException as error:
            print("FAILED", filename, "-", error)
            continue

        with open("data/raw/" + filename, "wb") as f:
            f.write(response.content)
        print("Saved", filename)


if __name__ == "__main__":
    main()