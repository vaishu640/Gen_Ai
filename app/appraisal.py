import json
from pathlib import Path

POINTS_FILE = Path(__file__).resolve().parent.parent / "data" / "appraisal_points.json"
MIN_MEMBERS = 5        # a local group needs at least 5 members
LAND_LIMIT = 0.5       # one member must not hold more than 50% of the group's land


def load_points():
    with open(POINTS_FILE, encoding="utf-8") as f:
        return json.load(f)


def check_group(farmers, points):
    n = len(farmers)
    total_land = sum((f["land"] or 0) for f in farmers)
    rows = []
    met_total = 0

    for f in farmers:
        missing = [p for p in points if not f["ticks"][p["id"]]]
        critical = [p for p in missing if p["critical"]]
        met_total = met_total + len(points) - len(missing)

        why = []
        if critical:
            why.append("Prohibited-substance point missing ("
                       + ", ".join(p["name"] for p in critical)
                       + "). The member can be excluded.")
        if total_land > 0 and f["land"] and f["land"] / total_land > LAND_LIMIT:
            why.append("Holds more than 50% of the group's land.")
        if missing and n - 1 < MIN_MEMBERS:
            why.append("If this farmer is excluded, the group drops below 5 members.")

        if why:
            status = "red"
        elif missing:
            status = "amber"
        else:
            status = "green"

        rows.append({
            "name": f["name"],
            "status": status,
            "met": len(points) - len(missing),
            "missing": [p["name"] for p in missing],
            "why": why,
        })

    score = round(100 * met_total / (n * len(points))) if n > 0 else 0
    red = sum(1 for r in rows if r["status"] == "red")
    amber = sum(1 for r in rows if r["status"] == "amber")

    if n < MIN_MEMBERS or red > 0:
        verdict = "Not ready for peer appraisal"
    elif amber > 0:
        verdict = "Almost ready"
    else:
        verdict = "Ready for peer appraisal"

    return {"n": n, "score": score, "red": red, "amber": amber,
            "verdict": verdict, "rows": rows}