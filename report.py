"""Render a completed audit as a markdown report."""
import json
from pathlib import Path
from runner import run_audit


def render(audit):
    t, c, v = audit["ticker"], audit["classification"], audit["verdict"]
    L = [f"# Bedrock Value Audit — {t}", ""]
    L += [f"**Sector Classification:** Type {c['sector_type']} — {c['justification']}", ""]
    L += [f"**Segment scoped:** {c['segment_scoped']}  ", f"**Method:** {c['method']}", ""]
    L += ["---", "", f"## Verdict: {v['verdict']}", "",
          f"**Catalyst:** {v['catalyst']}  ", f"**Timeline:** {v['timeline']}  ",
          f"**Confidence:** {v['confidence']}", "", v["reasoning"], ""]
    L += ["## Stages Executed", ""]
    for s in audit["stage_results"]:
        flag = " *(disqualifying)*" if s["disqualifying"] else ""
        L += [f"### Stage {s['id']} — {s['name']}{flag}", ""]
        for k, val in s["result"].items():
            if isinstance(val, list):
                L.append(f"- **{k}:**")
                L += [f"  - **{i['category']}** — {i['driver']} — \"{i['management_phrase']}\"" if isinstance(i, dict) and 'category' in i else f"  - {i}" for i in val]
            else:
                L.append(f"- **{k}:** {val}")
        L.append("")
    L += ["## Stages Not Run", ""]
    for s in audit["stages_missing"]:
        L.append(f"- **Stage {s['id']} — {s['name']}:** {s['reason']} ({', '.join(s['missing_requires'])})")
    L += ["", "## Downside Risk Register", ""]
    L += [f"{i}. {b}" for i, b in enumerate(v["thesis_breakers"], 1)]
    L += ["", "## Exit Criteria", "", v["exit_criteria"], ""]
    L += ["## Human Checks Outstanding", "", v["human_checks_outstanding"], ""]
    return "\n".join(L)


if __name__ == "__main__":
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    Path("reports").mkdir(exist_ok=True)
    out = Path(f"reports/{ticker}_audit.md")
    out.write_text(render(run_audit(ticker)))
    print(f"wrote {out}")
