#!/usr/bin/env python3
"""exam.json을 마크다운 문제지(+ 정답·해설)로 렌더링합니다.

사용법:
    python3 render_md.py generated.json [out.md]

- 라벨과 배점 표기는 language(ko/en)를 따릅니다.
- 보기 번호는 option_marker(circled/letter/number)를 따릅니다. 언어와 무관합니다.
- passage_group이 같은 문항은 지문을 묶음 첫 문항 앞에 한 번만 냅니다.
- meaning-write 문항은 문제지에서 뜻 칸을 비우고, 정답지에만 뜻을 냅니다.
"""
import json
import sys
from pathlib import Path

MARKERS = {
    "circled": ["①", "②", "③", "④", "⑤"],
    "letter": ["(A)", "(B)", "(C)", "(D)", "(E)"],
    "number": ["(1)", "(2)", "(3)", "(4)", "(5)"],
}

LABELS = {
    "ko": {
        "paper": "문제지", "key": "정답 및 해설", "pts": "[{}점]",
        "group": "[{}~{}] 다음 글을 읽고 물음에 답하시오.",
        "vocab_head": ["번호", "단어", "품사", "뜻", "예문"],
        "write_head": ["번호", "단어", "우리말 뜻"],
        "accept": "문맥에 맞는 유사한 뜻도 정답으로 인정한다.",
    },
    "en": {
        "paper": "Questions", "key": "Answer Key", "pts": "[{} points]",
        "group": "[{}–{}] Read the following passage and answer the questions.",
        "vocab_head": ["No.", "Word", "Part of Speech", "Meaning", "Example"],
        "write_head": ["No.", "Word", "Meaning"],
        "accept": "Meanings that fit the context are also accepted.",
    },
}


def fmt_points(p, L) -> str:
    if not p:
        return ""
    return " " + L["pts"].format(int(p) if float(p).is_integer() else p)


def table(head: list[str], rows: list[list[str]]) -> list[str]:
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return out


def render(exam: dict) -> str:
    L = LABELS[exam["language"]]
    nums = MARKERS[exam.get("option_marker", "circled")]
    items = exam["items"]
    group_ids: dict[str, list[int]] = {}
    for it in items:
        if it.get("passage_group"):
            group_ids.setdefault(it["passage_group"], []).append(it["id"])

    out = [f"# {exam['title']} — {L['paper']}", ""]
    seen_groups: set[str] = set()
    for it in items:
        g = it.get("passage_group")
        if g and g not in seen_groups:
            seen_groups.add(g)
            ids = group_ids[g]
            out += [f"**{L['group'].format(ids[0], ids[-1])}**", "", it["passage"], ""]
        out.append(f"**{it['id']}. {it['stem']}{fmt_points(it['points'], L)}**")
        out.append("")
        if it.get("passage") and not g:
            out += [it["passage"], ""]
        for i, o in enumerate(it.get("options") or []):
            out.append(f"{nums[i]} {o}  ")
        if it.get("vocab_entries"):
            if it["subtype"] == "meaning-write":
                rows = [[n, e["word"], "____________________"] for n, e in enumerate(it["vocab_entries"], 1)]
                out += table(L["write_head"], rows)
            else:
                rows = [[n, e["word"], e.get("pos", ""), e.get("meaning_ko") or e.get("meaning_en", ""), e["example"]]
                        for n, e in enumerate(it["vocab_entries"], 1)]
                out += table(L["vocab_head"], rows)
        out.append("")

    out += ["---", "", f"# {exam['title']} — {L['key']}", ""]
    for it in items:
        ans = it["answer"]
        if isinstance(ans, int) and it.get("options"):
            ans = nums[ans]
        if it["type"] == "vocab" and it.get("vocab_entries"):
            if it["subtype"] == "meaning-write":
                out.append(f"**{it['id']}.** {L['accept']}")
                out.append("")
                rows = [[n, e["word"], e.get("meaning_ko") or e.get("meaning_en", "")]
                        for n, e in enumerate(it["vocab_entries"], 1)]
                out += table(L["write_head"], rows)
                out.append("")
            continue
        out.append(f"**{it['id']}. {ans}** — {it['explanation']}")
        for note in it.get("distractor_notes", []):
            out.append(f"  - {note}")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    exam = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    md = render(exam)
    if len(sys.argv) >= 3:
        Path(sys.argv[2]).write_text(md, encoding="utf-8")
        print(f"저장: {sys.argv[2]}")
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        print(md, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
