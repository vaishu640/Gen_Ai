
import json

from app.llm import LLMError, ask_llm
from app.tools import call_tool

MAX_STEPS = 4


SYSTEM = """
You are an OrganicPath AI assistant.

You have two actions:

1. rag_search
Search PGS-India documents.

2. conversion_timeline
Calculate the PGS-Organic conversion date.

3. final
Give the final answer.

IMPORTANT:
- Return only plain JSON text.
- Never use built-in function calling.
- Never call external tools directly.
- Select an action by writing its JSON name.
- Use only the results provided to you.
- Never guess dates or rules.

Example:

{"action": "conversion_timeline",
 "args": {
     "joined_date": "2026-12-01",
     "crop_type": "annual"
 }}

For a final answer:

{"action": "final",
 "answer": "Your answer here."}
"""


def decide(question, steps, memory=""):

    user = "QUESTION: " + question + "\n\n"

    for step in steps:
        user += (
            "Previous action: " + step["tool"] + "\n"
            + "Result: " + json.dumps(step["result"]) + "\n\n"
        )

    if len(steps) >= MAX_STEPS:
        user += "Give the final answer now."
    else:
        user += "Choose the next action. Return JSON only."

    reply = ask_llm(SYSTEM, user)

    start = reply.find("{")
    end = reply.rfind("}")

    try:
        action = json.loads(reply[start:end + 1])
    except (ValueError, TypeError):
        return {
            "action": "final",
            "answer": reply
        }

    return action


def run_agent(question):

    steps = []

    while True:

        action = decide(question, steps)

        if action["action"] == "final":
            return {
                "answer": action.get("answer", ""),
                "steps": steps
            }

        if len(steps) >= MAX_STEPS:
            return {
                "answer": "Maximum steps reached.",
                "steps": steps
            }

        args = action.get("args", {})

        result = call_tool(action["action"], args)

        steps.append({
            "tool": action["action"],
            "args": args,
            "result": result
        })


if __name__ == "__main__":

    question = "What are the requirements for PGS-India organic certification?"

    try:
        result = run_agent(question)

        print("\nSTEPS:")
        for step in result["steps"]:
            print(step["tool"], "->", step["result"])

        print("\nFINAL ANSWER:")
        print(result["answer"])

    except LLMError as error:
        print("LLM ERROR:", error)
