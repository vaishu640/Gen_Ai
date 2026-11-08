import json

def load_records():
    with open("data/sample_records.json") as f:
        return json.load(f)

def search(records, word):
    found = []
    for r in records:
        if word.lower() in r["product"].lower():
            found.append(r)
    return found

def get_by_id(records, record_id):
    for r in records:
        if r["id"] == record_id:
            return r
    return None

def count_by(records, field):
    counts = {}
    for r in records:
        value = r[field]
        if value in counts:
            counts[value] = counts[value] + 1
        else:
            counts[value] = 1
    return counts