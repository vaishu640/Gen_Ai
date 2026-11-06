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