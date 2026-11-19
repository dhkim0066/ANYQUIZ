#!/usr/bin/env python3
"""exam.json(v2)을 마크다운 문제지로 렌더링합니다.

사용법:
    python3 render_md.py generated.json [out.md] [--paper-only]

- 머리: 제목, 이름·날짜·점수 줄, 영역별 배점표(sections가 있을 때).
- 라벨과 배점 표기는 language를, 정답·해설 쪽 라벨은 explanation_language를 따릅니다.
- 보기 번호는 option_marker를 따릅니다. 언어와 무관합니다.
- 유형별 출력은 references/schema.md "유형별 담는 법"을 따릅니다.
  (insertion·irrelevant는 보기 목록을 찍지 않음, 짝짓기는 표, word-bank는 보기 상자 등)
- --paper-only: 정답·해설 없이 문제지만 냅니다. 독립 풀이(검증 단계)에 넘길 때 씁니다.

export_docx.py가 이 파일의 build_blocks()를 불러 같은 구조로 DOCX를 만듭니다.
"""
import json
import re
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8")

MARKERS = {
    "circled": ["①", "②", "③", "④", "⑤"],
    "letter": ["(A)", "(B)", "(C)", "(D)", "(E)"],
    "number": ["(1)", "(2)", "(3)", "(4)", "(5)"],
}
POSITION = {"insertion", "irrelevant"}
MATCH = {"synonym-match", "definition-match"}

LABELS = {
    "ko": {
        "sheet": "이름: ______________　날짜: ______________　점수: ______ / {}점",
        "score_head": ["영역", "문항", "배점", "합계"],
        "range": "{}~{}번 ({}문항)", "one": "{}번",
        "each": "각 {}점", "mixed": "문항별 배점 참고", "none": "배점 없음", "total": "합계", "pts": "{}점",
        "pts_item": "[{}점]", "pts_part": "[{}점, 각 {}점]",
        "group": "[{}~{}] 다음 글을 읽고 물음에 답하시오.",
        "bank": "보기",
        "col": {"word": "단어", "pos": "품사", "meaning": "뜻", "example": "예문", "derived": "파생어"},
        "no": "번호", "ans": "답", "blank_head": "뜻",
        "key": "정답 및 해설", "quick": "정답",
        "accept": "문맥에 맞는 유사한 뜻도 정답으로 인정한다.",
    },
    "en": {
        "sheet": "Name: ______________　Date: ______________　Score: ______ / {}",
        "score_head": ["Section", "Questions", "Points", "Total"],
        "range": "{}–{} ({} questions)", "one": "{}",
        "each": "{} each", "mixed": "see each item", "none": "Not scored", "total": "Total", "pts": "{}",
        "pts_item": "[{} points]", "pts_part": "[{} points: {} each]",
        "group": "[{}–{}] Read the following passage and answer the questions.",
        "bank": "Word Bank",
        "col": {"word": "Word", "pos": "Part of Speech", "meaning": "Meaning", "example": "Example", "derived": "Related Forms"},
        "no": "No.", "ans": "Answer", "blank_head": "Meaning",
        "key": "Answer Key", "quick": "Answers",
        "accept": "Meanings that fit the context are also accepted.",
    },
}


def num(p) -> str:
    return str(int(p)) if float(p).is_integer() else str(p)


def default_labels(n: int, kind: str) -> list[str]:
    if kind == "left":
        return [f"({chr(97 + i)})" for i in range(n)]
    return [f"{i + 1}." for i in range(n)]


def match_labels(it: dict) -> tuple[list[str], list[str]]:
    L = it.get("match_left_labels") or default_labels(len(it["match_left"]), "left")
    R = it.get("match_right_labels") or default_labels(len(it["match_right"]), "right")
    return L, R


def points_label(it: dict, L: dict) -> str:
    if not it["points"]:
        return ""
    if it.get("points_per_part"):
        return " " + L["pts_part"].format(num(it["points"]), num(it["points_per_part"]))
    return " " + L["pts_item"].format(num(it["points"]))


def paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def score_table(exam: dict, L: dict) -> dict:
    by_id = {it["id"]: it for it in exam["items"]}
    rows, total = [], 0
    for s in exam["sections"]:
        its = [by_id[i] for i in range(s["first"], s["last"] + 1) if i in by_id]
        pts = [it["points"] for it in its]
        ssum = sum(pts)
        total += ssum
        rng = L["one"].format(s["first"]) if s["first"] == s["last"] else L["range"].format(s["first"], s["last"], len(its))
        if ssum == 0:
            how = L["none"]
        elif len(set(pts)) == 1 and len(pts) > 1:
            how = L["each"].format(num(pts[0]))
        elif len(pts) == 1:
            how = L["pts"].format(num(pts[0]))
        else:
            how = L["mixed"]
        rows.append([s["title"], rng, how, L["pts"].format(num(ssum)) if ssum else "-"])
    rows.append([f"**{L['total']}**", "", "", f"**{L['pts'].format(num(total))}**"])
    return {"k": "table", "head": L["score_head"], "rows": rows}


def answer_text(it: dict, nums: list[str]) -> str:
    a, st = it.get("answer"), it["subtype"]
    if a is None:
        return ""
    if st == "word-bank":
        return ", ".join(a)
    if st in MATCH:
        ll, rl = match_labels(it)
        return " ".join(f"{ll[i]}–{rl[x].rstrip('.')}" for i, x in enumerate(a))
    if isinstance(a, int) and it.get("options"):
        return nums[a]
    return str(a)


def build_blocks(exam: dict, paper_only: bool = False) -> list[dict]:
    """문제지를 블록 목록으로 만든다. 마크다운과 DOCX가 같은 목록을 쓴다."""
    L = LABELS[exam["language"]]
    K = LABELS[exam.get("explanation_language", exam["language"])]
    nums = MARKERS[exam.get("option_marker", "circled")]
    items = exam["items"]
    total = sum(it["points"] for it in items)
    group_ids: dict[str, list[int]] = {}
    for it in items:
        if it.get("passage_group"):
            group_ids.setdefault(it["passage_group"], []).append(it["id"])
    sec_start = {s["first"]: s for s in exam.get("sections", [])}

    B: list[dict] = [{"k": "title", "t": exam["title"]}, {"k": "p", "t": L["sheet"].format(num(total))}]
    if exam.get("sections"):
        B.append(score_table(exam, L))
    B.append({"k": "rule"})

    seen: set[str] = set()
    for it in items:
        st = it["subtype"]
        if it["id"] in sec_start:
            s = sec_start[it["id"]]
            B.append({"k": "section", "t": s["title"]})
            if s.get("instruction"):
                B.append({"k": "strong", "t": s["instruction"]})
        g = it.get("passage_group")
        if g and g not in seen:
            seen.add(g)
            ids = group_ids[g]
            B.append({"k": "strong", "t": it.get("group_instruction") or L["group"].format(ids[0], ids[-1])})
            B += [{"k": "p", "t": p} for p in paragraphs(it["passage"])]
            if it.get("footnote"):
                B.append({"k": "note", "t": it["footnote"]})

        stem = it.get("stem", "")
        head = stem if st == "word-list" else f"{it['id']}. {stem}".rstrip()
        B.append({"k": "stem", "t": head + points_label(it, L)})
        if it.get("given"):
            B.append({"k": "quote", "t": it["given"]})
        if it.get("word_bank"):
            B.append({"k": "quote", "t": f"**{L['bank']}**　" + " · ".join(it["word_bank"])})
        if it.get("passage") and not g:
            B += [{"k": "p", "t": p} for p in paragraphs(it["passage"])]
            if it.get("footnote"):
                B.append({"k": "note", "t": it["footnote"]})
        if it.get("prompt_text"):
            B.append({"k": "p", "t": it["prompt_text"]})
        opts = it.get("options")
        if opts and st not in POSITION:
            inline = all(len(o.split()) <= 3 for o in opts) and sum(len(o) for o in opts) <= 60
            B.append({"k": "opts", "items": [f"{nums[i]} {o}" for i, o in enumerate(opts)], "inline": inline})
        if st in MATCH:
            ll, rl = match_labels(it)
            left, right = it["match_left"], it["match_right"]
            rows = []
            for i in range(max(len(left), len(right))):
                rows.append([f"{ll[i]} {left[i]}" if i < len(left) else "",
                             "____" if i < len(left) else "",
                             f"{rl[i]} {right[i]}" if i < len(right) else ""])
            B.append({"k": "table", "head": [L["col"]["word"], L["ans"], ""], "rows": rows})
        if st == "meaning-write":
            rows = [[n, e["word"], "____________________"] for n, e in enumerate(it["vocab_entries"], 1)]
            B.append({"k": "table", "head": [L["no"], L["col"]["word"], L["blank_head"]], "rows": rows})
        if st == "word-list":
            cols = it["vocab_columns"]
            rows = [[n] + [", ".join(e[c]) if isinstance(e.get(c), list) else e.get(c, "") for c in cols]
                    for n, e in enumerate(it["vocab_entries"], 1)]
            B.append({"k": "table", "head": [L["no"]] + [L["col"][c] for c in cols], "rows": rows})

    if paper_only:
        return B

    B += [{"k": "break"}, {"k": "title", "t": f"{exam['title']} — {K['key']}"}]
    quick = [f"{it['id']}{answer_text(it, nums)}" for it in items
             if isinstance(it.get("answer"), int) and it.get("options")]
    if quick:
        B.append({"k": "strong", "t": f"{K['quick']}: " + " ".join(quick)})
    for it in items:
        st = it["subtype"]
        if st == "word-list":
            continue
        if st == "meaning-write":
            B.append({"k": "p", "t": f"**{it['id']}.** {K['accept']}"})
            rows = [[n, e["word"], e.get("meaning", "")] for n, e in enumerate(it["vocab_entries"], 1)]
            B.append({"k": "table", "head": [K["no"], K["col"]["word"], K["col"]["meaning"]], "rows": rows})
            continue
        line = f"**{it['id']}. {answer_text(it, nums)}**"
        if it.get("explanation"):
            line += f" — {it['explanation']}"
        B.append({"k": "p", "t": line})
        if st in MATCH and isinstance(it.get("answer"), list):
            ll, rl = match_labels(it)
            pairs = [f"{ll[i]} {it['match_left'][i]} ↔ {rl[x]} {it['match_right'][x]}" for i, x in enumerate(it["answer"])]
            B.append({"k": "bullets", "items": pairs})
        notes = it.get("distractor_notes") or []
        opts = it.get("options")
        if notes and opts and isinstance(it.get("answer"), int):
            wrong = [i for i in range(len(opts)) if i != it["answer"]]
            labels = [opts[i] if st in POSITION else nums[i] for i in wrong]
            if len(notes) == len(wrong):
                B.append({"k": "bullets", "items": [f"{lb} {n}" for lb, n in zip(labels, notes)]})
            else:
                B.append({"k": "bullets", "items": notes})
    return B


def md_table(head: list, rows: list) -> list[str]:
    out = ["| " + " | ".join(str(h) for h in head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(str(c).replace("|", "\\|") for c in r) + " |" for r in rows]
    return out


def to_markdown(blocks: list[dict]) -> str:
    out: list[str] = []
    for b in blocks:
        k = b["k"]
        if k == "title":
            out += [f"# {b['t']}", ""]
        elif k == "section":
            out += [f"## {b['t']}", ""]
        elif k in ("strong", "stem"):
            out += [f"**{b['t']}**", ""]
        elif k == "p":
            out += [b["t"], ""]
        elif k == "note":
            out += [f"*{b['t'].strip('*')}*", ""]
        elif k == "quote":
            out += ["> " + ln for ln in b["t"].splitlines()] + [""]
        elif k == "opts":
            out += ["　".join(b["items"]), ""] if b["inline"] else [x + "  " for x in b["items"]] + [""]
        elif k == "table":
            out += md_table(b["head"], b["rows"]) + [""]
        elif k == "bullets":
            out += [f"  - {x}" for x in b["items"]] + [""]
        elif k in ("rule", "break"):
            out += ["---", ""]
    return "\n".join(out).rstrip() + "\n"


def main() -> int:
    flags = [a for a in sys.argv[1:] if a.startswith("-")]
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if not args or "-h" in flags or "--help" in flags:
        print(__doc__)
        return 0 if flags else 1
    try:
        exam = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"읽을 수 없음: {args[0]}: {e}", file=sys.stderr)
        return 1
    if exam.get("schema_version") != 2:
        print("schema_version 2가 아닙니다. references/schema.md를 따라 다시 작성하세요.", file=sys.stderr)
        return 1
    md = to_markdown(build_blocks(exam, paper_only="--paper-only" in flags))
    if len(args) >= 2:
        Path(args[1]).write_text(md, encoding="utf-8")
        print(f"저장: {args[1]}")
    else:
        print(md, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
