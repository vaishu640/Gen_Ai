import json
import sys
import uuid
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))        # so "from app...." works when Streamlit runs this file

import pandas as pd
import requests
import streamlit as st

from app.appraisal import assess_group, load_points

FEEDBACK_FILE = ROOT / "data" / "feedback.jsonl"

st.set_page_config(page_title="OrganicPath", page_icon="🌱", layout="wide")

# ---------- memory of the page ----------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "ratings" not in st.session_state:
    st.session_state.ratings = {}
if "pending" not in st.session_state:
    st.session_state.pending = None
if "session_id" not in st.session_state:
    st.session_state.session_id = "ui-" + uuid.uuid4().hex[:8]
if "editor_version" not in st.session_state:
    st.session_state.editor_version = 0

# ---------- sidebar ----------
st.sidebar.title("🌱 OrganicPath")
st.sidebar.caption("Helps a PGS-India farmer group get certified.")
api_url = st.sidebar.text_input("API address", "http://127.0.0.1:8000")
mode = st.sidebar.radio("Chat uses", ["/ask  (answer with citations)",
                                      "/agent  (tools + approval step)"])

if st.sidebar.button("Check API connection"):
    try:
        health = requests.get(api_url.rstrip("/") + "/health", timeout=5).json()
        st.sidebar.success("API is running: " + str(health))
    except Exception as error:
        st.sidebar.error("Cannot reach the API: " + str(error))

if st.sidebar.button("Start a new conversation"):
    st.session_state.messages = []
    st.session_state.pending = None
    st.session_state.session_id = "ui-" + uuid.uuid4().hex[:8]
    st.rerun()


# ---------- helpers for the chat ----------
def post(path, payload):
    try:
        r = requests.post(api_url.rstrip("/") + path, json=payload, timeout=180)
    except requests.exceptions.RequestException as error:
        return None, "Cannot reach the API. Is the server running? (" + str(error) + ")"
    if r.status_code != 200:
        try:
            detail = r.json().get("detail", r.text)
        except ValueError:
            detail = r.text
        return None, "API error " + str(r.status_code) + ": " + str(detail)
    return r.json(), None


def add_message(role, content, **extra):
    msg = {"id": uuid.uuid4().hex[:8], "role": role, "content": content}
    msg.update(extra)
    st.session_state.messages.append(msg)


def save_feedback(message_id, rating):
    msg = next((m for m in st.session_state.messages if m["id"] == message_id), None)
    if msg is None:
        return
    record = {
        "time": datetime.now().isoformat(timespec="seconds"),
        "rating": rating,
        "question": msg.get("question", ""),
        "answer": msg["content"],
        "endpoint": msg.get("endpoint", ""),
    }
    with open(FEEDBACK_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    st.session_state.ratings[message_id] = rating


def show_message(msg):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] != "assistant" or msg.get("error"):
            return

        if msg.get("confidence"):
            st.caption("Confidence: " + msg["confidence"])

        if msg.get("citations"):
            st.markdown("**Sources**")
            for c in msg["citations"]:
                label = c["title"] + ", page " + str(c["page"])
                if c.get("source_url"):
                    label = "[" + label + "](" + c["source_url"] + ")"
                st.markdown("- " + label)
                if c.get("snippet"):
                    st.caption(c["snippet"])

        if msg.get("steps"):
            with st.expander("What the agent did"):
                for step in msg["steps"]:
                    st.write("**" + step["tool"] + "**", step["args"])
                    st.json(step["result"])

        rating = st.session_state.ratings.get(msg["id"])
        if rating:
            st.caption("Feedback saved: " + ("👍" if rating == "up" else "👎"))
        else:
            c1, c2, _ = st.columns([1, 1, 8])
            c1.button("👍", key="up-" + msg["id"], on_click=save_feedback, args=(msg["id"], "up"))
            c2.button("👎", key="down-" + msg["id"], on_click=save_feedback, args=(msg["id"], "down"))


def citations_from_steps(steps):
    found, seen = [], set()
    for step in steps:
        result = step.get("result")
        if step.get("tool") == "rag_search" and isinstance(result, dict):
            for c in result.get("citations", []):
                key = (c["title"], c["page"])
                if key not in seen:
                    seen.add(key)
                    found.append(c)
    return found


def handle_agent_result(data, question):
    if data.get("status") == "waiting_for_approval":
        st.session_state.pending = data["pending"]
        return
    st.session_state.pending = None
    steps = data.get("steps", [])
    add_message("assistant", data.get("answer", ""), question=question, endpoint="/agent",
                steps=steps, citations=citations_from_steps(steps))


def ask_api(question):
    add_message("user", question)
    st.session_state.last_question = question
    use_agent = mode.startswith("/agent")
    with st.spinner("Working on it ..."):
        if use_agent:
            data, error = post("/agent", {"session_id": st.session_state.session_id,
                                          "question": question})
        else:
            data, error = post("/ask", {"question": question, "k": 5, "chunk_words": 60})

    if error:
        add_message("assistant", error, error=True)
    elif use_agent:
        handle_agent_result(data, question)
    else:
        add_message("assistant", data["answer"], question=question, endpoint="/ask",
                    confidence=data.get("confidence"), citations=data.get("citations", []))


def send_decision(decision):
    data, error = post("/agent", {"session_id": st.session_state.session_id,
                                  "decision": decision})
    st.session_state.pending = None
    if error:
        add_message("assistant", error, error=True)
    else:
        handle_agent_result(data, st.session_state.get("last_question", ""))
    st.rerun()


def show_pending():
    p = st.session_state.pending
    if not p:
        return
    with st.chat_message("assistant"):
        st.warning("The agent wants to run **" + str(p.get("tool")) + "**. "
                   + str(p.get("message", "")))
        st.json(p.get("args", {}))
        c1, c2, _ = st.columns([1, 1, 6])
        if c1.button("✅ Approve", key="approve"):
            send_decision("approve")
        if c2.button("❌ Reject", key="reject"):
            send_decision("reject")


# ---------- helpers for the checklist ----------
def blank_df(points, n=12):
    rows = []
    for i in range(n):
        row = {"Farmer": "Farmer " + str(i + 1), "Land (acres)": None}
        for p in points:
            row[p["id"]] = False
        rows.append(row)
    return pd.DataFrame(rows)


def demo_df(points):
    lands = [3, 2.5, 4, 2, 30, 3, 2.5, 3.5, 2, 3, 2.5, 3]
    rows = []
    for i in range(12):
        row = {"Farmer": "Farmer " + str(i + 1), "Land (acres)": lands[i]}
        for p in points:
            row[p["id"]] = True
        rows.append(row)
    # a few gaps so the flags show up (demo data, not real farmers)
    for index, pid in [(2, "soil_fertility"), (6, "diversity"), (8, "livestock"), (8, "soil_water")]:
        if pid in rows[index]:
            rows[index][pid] = False
    return pd.DataFrame(rows)


# ---------- the page ----------
st.title("🌱 OrganicPath")
tab_chat, tab_check = st.tabs(["💬 Chat", "✅ Peer-appraisal readiness checklist"])

with tab_chat:
    st.subheader("Ask about PGS-India certification")
    st.caption("Answers come only from the official PGS-India documents. "
               "If they do not contain the answer, the bot says it does not know.")
    for message in st.session_state.messages:
        show_message(message)
    show_pending()

    question = st.chat_input("Ask a question ...", disabled=bool(st.session_state.pending))
    if question:
        ask_api(question)
        st.rerun()

with tab_check:
    st.subheader("Peer-appraisal readiness checklist")
    try:
        points = load_points()
    except (OSError, ValueError) as error:
        st.error("Could not read data/appraisal_points.json: " + str(error))
        points = []

    if points:
        st.caption("Tick every standard point a farmer has met. The points come from "
                   "PGS-India Standards, Appendix 1. Add or remove farmers in the table.")

        with st.expander("What does each point mean?"):
            for p in points:
                badge = " 🔴 prohibited-substance point" if p.get("critical") else ""
                st.markdown("**" + p["name"] + "**" + badge)
                st.caption(p["check"] + "  (" + p["source"] + ")")

        if "group_df" not in st.session_state:
            st.session_state.group_df = demo_df(points)

        b1, b2, _ = st.columns([2, 2, 6])
        if b1.button("Load demo group (not real data)"):
            st.session_state.group_df = demo_df(points)
            st.session_state.editor_version += 1
            st.rerun()
        if b2.button("Start a blank group of 12"):
            st.session_state.group_df = blank_df(points)
            st.session_state.editor_version += 1
            st.rerun()

        config = {
            "Farmer": st.column_config.TextColumn("Farmer", required=True),
            "Land (acres)": st.column_config.NumberColumn("Land (acres)", min_value=0.0, step=0.5),
        }
        for p in points:
            config[p["id"]] = st.column_config.CheckboxColumn(p["name"], default=False, help=p["check"])

        edited = st.data_editor(st.session_state.group_df, column_config=config,
                                num_rows="dynamic",
                                key="editor-" + str(st.session_state.editor_version))

        farmers = []
        for _, row in edited.iterrows():
            name = str(row["Farmer"]).strip()
            if name in ("", "nan", "None"):
                continue
            land = row["Land (acres)"]
            land = None if pd.isna(land) else float(land)
            ticks = {}
            for p in points:
                value = row[p["id"]]
                ticks[p["id"]] = False if pd.isna(value) else bool(value)
            farmers.append({"name": name, "land": land, "ticks": ticks})

        result = assess_group(farmers, points)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Group readiness score", str(result["score"]) + " %")
        m2.metric("Farmers", result["n"])
        m3.metric("🔴 Red flags", result["counts"]["red"])
        m4.metric("🟠 Needs work", result["counts"]["amber"])
        st.progress(result["score"] / 100)

        getattr(st, result["verdict_level"])("**" + result["verdict"] + "**")
        for level, text in result["messages"]:
            getattr(st, level)(text)

        icons = {"red": "🔴 Red flag", "amber": "🟠 Needs work", "green": "🟢 Ready"}
        table = []
        for r in result["farmers"]:
            table.append({
                "Farmer": r["name"],
                "Status": icons[r["status"]],
                "Points met": str(r["met"]) + " / " + str(len(points)),
                "Missing": ", ".join(r["missing"]) or "-",
                "Why": " ".join(r["reasons"]) or "-",
            })
        st.dataframe(pd.DataFrame(table), hide_index=True)

        st.markdown("**How many farmers meet each point**")
        st.dataframe(pd.DataFrame(result["by_point"]), hide_index=True)

        with st.expander("How the score and the red flags work"):
            st.markdown(
                "- **Score** = points met by all farmers, out of all points possible.\n"
                "- 🔴 **Red flag** = a prohibited-substance point is missing (serious "
                "non-compliance: the member can be excluded and the Regional Council may "
                "withhold approval for the whole group), or the farmer holds more than 50% of "
                "the group's land (Guidelines Edition 2, s4.1(e)), or a missing point means "
                "excluding this farmer would leave fewer than 5 members (s4.1(a), s5.1).\n"
                "- 🟠 **Needs work** = another point is missing, or the farmer holds more than "
                "one third of the land (the FAQ page limit).\n"
                "- 🟢 **Ready** = every point is met."
            )