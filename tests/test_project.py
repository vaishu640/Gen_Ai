import json

from fastapi.testclient import TestClient

from app import agent_loop, rag
from app.appraisal import check_group, load_points
from app.llm import LLMError
from app.main import app as fastapi_app
from app.records import get_by_id, load_records
from app.smart_search import SmartSearch
from app.tools import call_tool

client = TestClient(fastapi_app)
ASK = {
    "question": "How many farmers are needed to form a PGS-India local group?",
    "k": 3,
    "chunk_words": 120,
}


def fake_model(text):
    def fake(system, user, provider=None):
        return text

    return fake


# ---------- records ----------
def test_load_records_returns_a_non_empty_list():
    records = load_records()
    assert isinstance(records, list)
    assert len(records) > 0


def test_get_by_id_finds_a_record_and_returns_none_for_unknown_id():
    records = load_records()
    assert get_by_id(records, records[0]["id"]) == records[0]
    assert get_by_id(records, -999) is None


def test_rule_records_have_all_six_fields():
    with open("data/records.json", encoding="utf-8") as f:
        rule_records = json.load(f)
    assert len(rule_records) >= 15
    for record in rule_records:
        for field in ("topic", "rule", "applies_to", "stage", "source_doc", "source_url"):
            assert record[field]


# ---------- search ----------
def test_search_finds_the_group_size_rule():
    with open("data/records.json", encoding="utf-8") as f:
        rule_records = json.load(f)
    engine = SmartSearch(rule_records)
    results = engine.search("How many farmers are needed to form a PGS-India local group?")
    assert results
    assert "group" in results[0]["topic"].lower()


def test_search_returns_nothing_for_an_out_of_domain_question():
    with open("data/records.json", encoding="utf-8") as f:
        rule_records = json.load(f)
    engine = SmartSearch(rule_records)
    assert engine.search("Which restaurant serves the best pizza in Mumbai?") == []


# ---------- API ----------
def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["records"] > 0


def test_ask_returns_an_answer_with_citations(monkeypatch):
    reply = json.dumps({
        "answerable": True,
        "answer": "A local group needs at least 5 members [1].",
        "cited": [1],
        "confidence": "high",
    })
    monkeypatch.setattr(rag, "ask_llm", fake_model(reply))
    body = client.post("/ask", json=ASK).json()
    assert body["answerable"] is True
    assert "5 members" in body["answer"]
    assert body["citations"][0]["page"] == 23


def test_ask_says_i_dont_know_when_the_model_cannot_answer(monkeypatch):
    reply = json.dumps({
        "answerable": False,
        "answer": "I don't know. This is not in the PGS-India documents I have.",
        "cited": [],
        "confidence": "low",
    })
    monkeypatch.setattr(rag, "ask_llm", fake_model(reply))
    body = client.post("/ask", json=ASK).json()
    assert body["answerable"] is False
    assert body["answer"].startswith("I don't know")
    assert body["citations"] == []


def test_ask_returns_502_when_the_llm_fails(monkeypatch):
    def broken(system, user, provider=None):
        raise LLMError("the model is down")

    monkeypatch.setattr(rag, "ask_llm", broken)
    assert client.post("/ask", json=ASK).status_code == 502


# ---------- the agent tool ----------
def test_conversion_timeline_for_an_annual_crop():
    result = call_tool(
        "conversion_timeline", {"joined_date": "2026-12-01", "crop_type": "annual"}
    )
    assert result["conversion_months"] == 24
    assert result["earliest_pgs_organic"] == "2028-12-01"


def test_conversion_timeline_for_a_perennial_crop():
    result = call_tool(
        "conversion_timeline", {"joined_date": "2026-12-01", "crop_type": "perennial"}
    )
    assert result["conversion_months"] == 36
    assert result["earliest_pgs_organic"] == "2029-12-01"


def test_conversion_timeline_rejects_a_bad_crop_type():
    result = call_tool(
        "conversion_timeline", {"joined_date": "2026-12-01", "crop_type": "banana tree"}
    )
    assert "error" in result


def test_unknown_tool_returns_an_error():
    assert "error" in call_tool("make_coffee", {})


def test_agent_calls_the_date_tool_and_then_answers(monkeypatch):
    replies = iter([
        json.dumps({
            "action": "conversion_timeline",
            "args": {"joined_date": "2026-12-01", "crop_type": "annual"},
        }),
        json.dumps({
            "action": "final",
            "answer": "You can sell as PGS-Organic from 2028-12-01.",
        }),
    ])
    monkeypatch.setattr(agent_loop, "ask_llm", lambda system, user, provider=None: next(replies))
    result = agent_loop.run_agent("When can we sell as PGS-Organic?")
    assert result["steps"][0]["tool"] == "conversion_timeline"
    assert result["steps"][0]["result"]["earliest_pgs_organic"] == "2028-12-01"
    assert "2028-12-01" in result["answer"]


# ---------- the checklist ----------
def make_farmers(points, count=12):
    return [
        {"name": "Farmer " + str(i + 1), "land": 3, "ticks": {p["id"]: True for p in points}}
        for i in range(count)
    ]


def test_group_with_every_point_met_is_ready():
    points = load_points()
    result = check_group(make_farmers(points), points)
    assert result["score"] == 100
    assert result["verdict"] == "Ready for peer appraisal"


def test_missing_prohibited_substance_point_gives_a_red_flag():
    points = load_points()
    farmers = make_farmers(points)
    critical_id = next(p["id"] for p in points if p["critical"])
    farmers[2]["ticks"][critical_id] = False
    result = check_group(farmers, points)
    assert result["rows"][2]["status"] == "red"
    assert result["red"] == 1