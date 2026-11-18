import calendar
import json
import re
from datetime import date, datetime, timedelta


def add_months(start, months):
    m = start.month - 1 + months
    year = start.year + m // 12
    month = m % 12 + 1
    day = min(start.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def read_months(crop_type):
    """Read the conversion period (in months) from records.json."""
    default = 36 if crop_type == "perennial" else 24
    try:
        with open("data/records.json", encoding="utf-8") as f:
            records = json.load(f)
    except (OSError, ValueError):
        return default, "default (records.json not found)"

    for r in records:
        topic = r["topic"].lower()
        if "conversion period" in topic and crop_type in topic:
            found = re.search(r"(\d+) months", r["rule"])
            if found:
                return int(found.group(1)), r["source_doc"]
    return default, "default (no conversion record in records.json)"


def conversion_timeline(joined_date, crop_type):
    """PGS-Green window and the earliest PGS-Organic date."""
    try:
        joined = datetime.strptime(str(joined_date), "%Y-%m-%d").date()
    except ValueError:
        return {"error": "joined_date must look like 2026-12-01"}

    crop = str(crop_type).lower()
    if crop not in ("annual", "perennial"):
        return {"error": 'crop_type must be "annual" or "perennial"'}

    months, source = read_months(crop)
    organic = add_months(joined, months)
    green_end = organic - timedelta(days=1)

    return {
        "crop_type": crop,
        "conversion_months": months,
        "pgs_green_from": str(joined),
        "pgs_green_until": str(green_end),
        "earliest_pgs_organic": str(organic),
        "source": source,
        "note": "Conversion starts on the date the Regional Council registers the "
                "group. PGS-Organic also needs no major non-compliance.",
    }


def rag_search(question):
    """My Day 8 RAG bot (the winning config B: 60 words, top 5)."""
    from app.rag import answer_question
    result = answer_question(question, 5, 60)
    return {
        "answer": result["answer"],
        "answerable": result["answerable"],
        "citations": [{"title": c["title"], "page": c["page"]}
                      for c in result["citations"]],
    }


def call_tool(name, args):
    tools = {"rag_search": rag_search, "conversion_timeline": conversion_timeline}
    if name not in tools:
        return {"error": "unknown tool " + str(name)}
    try:
        return tools[name](**args)
    except Exception as error:
        return {"error": str(error)}


if __name__ == "__main__":
    print(conversion_timeline("2026-12-01", "annual"))
    print(conversion_timeline("2026-12-01", "perennial"))