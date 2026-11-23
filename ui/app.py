import json
import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))          # so "from app...." works inside Streamlit

import pandas as pd
import requests
import streamlit as st

from app.appraisal import check_group, load_points

# In Docker the API is in another container, so its address comes from a setting.
API = os.environ.get("API_URL", "http://127.0.0.1:8000")
FEEDBACK_FILE = ROOT / "data" / "feedback.jsonl"

st.set_page_config(page_title="OrganicPath", page_icon="🌱", layout="wide")
st.title("🌱 OrganicPath")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "version" not in st.session_state:
    st.session_state.version = 0


def save_feedback(index, rating):
    msg = st.session_state.messages[index]
    record = {
        "time": datetime.now().isoformat(timespec="seconds"),
        "rating": rating,
        "question": msg.get("question", ""),
        "answer": msg["content"],
    }
    with open(FEEDBACK_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    msg["rating"] = rating


def demo_group(points):
    lands = [3, 2.5, 4, 2, 6, 3, 2.5, 3.5, 2, 3, 2.5, 3]
    rows = []
    for i in range(12):
        row = {"Farmer": "Farmer " + str(i + 1), "Land (acres)": lands[i]}
        for p in points:
            row[p["id"]] = True
        rows.append(row)

    # a few gaps so the flags show up (demo data, not real farmers)
    gaps = [(2, "soil_fertility"),   # Farmer 3: a prohibited-substance point missing
            (6, "diversity"),        # Farmer 7: a smaller point missing
            (8, "livestock")]        # Farmer 9: a smaller point missing
    for index, point_id in gaps:
        if point_id in rows[index]:
            rows[index][point_id] = False
    return pd.DataFrame(rows)


tab_chat, tab_check = st.tabs(["💬 Chat", "✅ Peer-appraisal readiness checklist"])

# ---------------- Chat ----------------
with tab_chat:
    st.caption("Answers come only from the official PGS-India documents. "
               "If they do not contain the answer, the bot says it does not know.")

    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            for c in msg.get("citations", []):
                st.caption("📄 " + c["title"] + ", page " + str(c["page"]))
            if msg["role"] == "assistant" and not msg.get("error"):
                if msg.get("rating"):
                    st.caption("Feedback saved: " + msg["rating"])
                else:
                    col1, col2, _ = st.columns([1, 1, 8])
                    col1.button("👍", key="up" + str(i), on_click=save_feedback, args=(i, "up"))
                    col2.button("👎", key="down" + str(i), on_click=save_feedback, args=(i, "down"))

        question = st.chat_input("Ask a question about PGS-India certification", max_chars=500)
    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        try:
            r = requests.post(API + "/ask",
                              json={"question": question, "k": 5, "chunk_words": 60},
                              timeout=180)
            if r.status_code == 200:
                data = r.json()
                st.session_state.messages.append({
                    "role": "assistant", "content": data["answer"],
                    "citations": data.get("citations", []), "question": question})
            else:
                st.session_state.messages.append({
                    "role": "assistant", "error": True,
                    "content": "API error " + str(r.status_code) + ": " + r.text[:300]})
        except requests.exceptions.RequestException:
            st.session_state.messages.append({
                "role": "assistant", "error": True,
                "content": "Cannot reach the API. Is the server running?"})
        st.rerun()

# ---------------- Checklist ----------------
with tab_check:
    points = load_points()
    st.caption("Tick every standard point a farmer has met. Add or remove farmers in the table.")

    with st.expander("What does each point mean?"):
        for p in points:
            badge = "  🔴 prohibited-substance point" if p["critical"] else ""
            st.markdown("**" + p["name"] + "**" + badge)
            st.caption(p["check"] + " (" + p["source"] + ")")

    if "group_df" not in st.session_state:
        st.session_state.group_df = demo_group(points)

    if st.button("Reset to the demo group (not real data)"):
        st.session_state.group_df = demo_group(points)
        st.session_state.version += 1
        st.rerun()

    config = {"Land (acres)": st.column_config.NumberColumn("Land (acres)", min_value=0.0, step=0.5)}
    for p in points:
        config[p["id"]] = st.column_config.CheckboxColumn(p["name"], default=False, help=p["check"])

    table = st.data_editor(st.session_state.group_df, column_config=config,
                           num_rows="dynamic", key="editor" + str(st.session_state.version))

    farmers = []
    for _, row in table.iterrows():
        name = str(row["Farmer"]).strip()
        if name in ("", "nan", "None"):
            continue
        land = None if pd.isna(row["Land (acres)"]) else float(row["Land (acres)"])
        ticks = {}
        for p in points:
            value = row[p["id"]]
            ticks[p["id"]] = False if pd.isna(value) else bool(value)
        farmers.append({"name": name, "land": land, "ticks": ticks})

    result = check_group(farmers, points)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Group readiness score", str(result["score"]) + " %")
    c2.metric("Farmers", result["n"])
    c3.metric("🔴 Red flags", result["red"])
    c4.metric("🟠 Needs work", result["amber"])
    st.progress(result["score"] / 100)

    if result["verdict"].startswith("Not"):
        st.error("**" + result["verdict"] + "**")
    elif result["verdict"] == "Almost ready":
        st.warning("**" + result["verdict"] + "**")
    else:
        st.success("**" + result["verdict"] + "**")
    if result["n"] < 5:
        st.error("A local group needs at least 5 members.")

    labels = {"red": "🔴 Red flag", "amber": "🟠 Needs work", "green": "🟢 Ready"}
    rows = []
    for r in result["rows"]:
        rows.append({
            "Farmer": r["name"],
            "Status": labels[r["status"]],
            "Points met": str(r["met"]) + " / " + str(len(points)),
            "Missing": ", ".join(r["missing"]) or "-",
            "Why": " ".join(r["why"]) or "-",
        })
    st.dataframe(pd.DataFrame(rows), hide_index=True)

    with st.expander("How the red flags work"):
        st.markdown(
            "- 🔴 **Red flag**: a prohibited-substance point is missing, or the farmer holds "
            "more than 50% of the group's land, or excluding this farmer would leave fewer "
            "than 5 members.\n"
            "- 🟠 **Needs work**: another point is missing.\n"
            "- 🟢 **Ready**: every point is met.\n"
            "- **Score** = points met by all farmers out of all points possible.")