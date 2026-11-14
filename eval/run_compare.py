import time
from app.main import chat, ChatRequest

QUESTIONS = [
    "How many farmers are needed to form a PGS-India local group?",
    "What is the difference between PGS-Green and PGS-Organic certificates?",
    "Can one farmer's mistake cancel organic status for the whole village?",
    "Our 12-member group in Kopargaon joins in December 2026 and grows sugarcane and vegetables. When can we first sell as PGS-Organic, and what documents do we keep till then?",
    "Compare PGS-India organic certification with the new Natural Farming Certification. Which suits a group using jeevamrut?",
    "Which shop in Pune pays the highest price for PGS-certified jaggery?",
    "Can one member of our group own most of the group's land?",
    "Can I use chemical fertilizer on one plot and keep my other plots organic?",
    "How many group meetings must we hold each year and how many must each member attend?",
    "Can I export my PGS-certified produce as organic?",
]


def cell(text):
    return str(text).replace("|", "/").replace("\n", " ")


lines = [
    "# Prompt comparison: v1 vs v2",
    "",
    "Same 10 questions, same records, same model. Only the task prompt changes.",
    "- v1 = short prompt (`prompts/task_v1.md`)",
    "- v2 = step-by-step strict prompt (`prompts/task_v2.md`)",
    "",
    "| # | Question | v1 answer | v1 conf | v2 answer | v2 conf |",
    "|---|----------|-----------|---------|-----------|---------|",
]

for number, question in enumerate(QUESTIONS, 1):
    row = [str(number), cell(question)]
    for version in ("v1", "v2"):
        try:
            result = chat(ChatRequest(question=question, prompt_version=version))
            row.append(cell(result["answer"]))
            row.append(result["confidence"])
        except Exception as error:
            row.append("ERROR: " + cell(error))
            row.append("-")
        time.sleep(6)
    lines.append("| " + " | ".join(row) + " |")
    print("done question", number)

lines += ["", "## My verdict", "", "(fill this in after reading the table)", ""]

with open("eval/prompt_compare.md", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("Saved eval/prompt_compare.md")