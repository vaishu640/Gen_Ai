
from operator import add
from typing import Annotated, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from app.agent_loop import decide
from app.tools import call_tool


class State(TypedDict, total=False):
    question: str
    memory: Annotated[list, add]
    steps: list
    action: dict
    approved: bool
    answer: str


def plan(state):
    memory = "\n".join(state.get("memory", [])[-6:])

    action = decide(
        state["question"],
        state.get("steps", []),
        memory
    )

    return {"action": action}


def route(state):
    name = state["action"]["action"]

    if name == "final":
        return "respond"

    if name == "conversion_timeline":
        return "approve"

    return "run_tool"


def approve(state):
    action = state["action"]

    decision = interrupt({
        "message": "Do you approve this date calculation?",
        "tool": action["action"],
        "args": action.get("args", {}),
    })

    if str(decision).lower() == "approve":
        return {"approved": True}

    step = {
        "tool": action["action"],
        "args": action.get("args", {}),
        "result": {
            "error": "The user did not approve, so it was not run."
        }
    }

    return {
        "approved": False,
        "steps": state.get("steps", []) + [step]
    }


def after_approve(state):
    return "run_tool" if state["approved"] else "plan"


def run_tool(state):
    action = state["action"]
    args = action.get("args") or {}

    step = {
        "tool": action["action"],
        "args": args,
        "result": call_tool(action["action"], args)
    }

    return {
        "steps": state.get("steps", []) + [step]
    }


def respond(state):
    answer = str(state["action"].get("answer", ""))

    return {
        "answer": answer,
        "memory": [
            "User: " + state["question"],
            "Assistant: " + answer
        ]
    }


builder = StateGraph(State)

builder.add_node("plan", plan)
builder.add_node("approve", approve)
builder.add_node("run_tool", run_tool)
builder.add_node("respond", respond)

builder.add_edge(START, "plan")

builder.add_conditional_edges(
    "plan",
    route,
    {
        "respond": "respond",
        "approve": "approve",
        "run_tool": "run_tool"
    }
)

builder.add_conditional_edges(
    "approve",
    after_approve,
    {
        "run_tool": "run_tool",
        "plan": "plan"
    }
)

builder.add_edge("run_tool", "plan")
builder.add_edge("respond", END)

graph = builder.compile(checkpointer=MemorySaver())


def config(session_id):
    return {
        "configurable": {
            "thread_id": session_id
        }
    }


def waiting(session_id):
    """Check whether the session is waiting for approval."""

    snapshot = graph.get_state(config(session_id))

    for task in snapshot.tasks:
        for item in task.interrupts:
            return item.value

    return None


def result(session_id):
    pending = waiting(session_id)

    if pending:
        return {
            "status": "waiting_for_approval",
            "pending": pending
        }

    values = graph.get_state(config(session_id)).values

    return {
        "status": "done",
        "answer": values.get("answer", ""),
        "steps": values.get("steps", []),
        "turns_remembered": len(values.get("memory", [])) // 2
    }


def ask_agent(session_id, question):
    if waiting(session_id):
        raise ValueError(
            "This session is waiting for approval. Send decision approve or reject."
        )

    graph.invoke(
        {
            "question": question,
            "steps": []
        },
        config(session_id)
    )

    return result(session_id)


def send_decision(session_id, decision):
    if not waiting(session_id):
        raise ValueError(
            "Nothing is waiting for approval in this session."
        )

    graph.invoke(
        Command(resume=decision),
        config(session_id)
    )

    return result(session_id)
