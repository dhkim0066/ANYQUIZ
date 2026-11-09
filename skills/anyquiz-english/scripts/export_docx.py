#!/usr/bin/env python3
"""exam.json을 DOCX 문제지(+ 정답·해설 페이지)로 내보냅니다.

사용법:
    python3 export_docx.py generated.json out.docx

assets/exam-template.docx가 있으면 그 스타일을 쓰고, 없으면 기본 문서로 만듭니다.
python-docx가 필요합니다: pip install python-docx
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
TEMPLATE = HERE.parent / "assets" / "exam-template.docx"

KO_NUM = ["①", "②", "③", "④", "⑤"]
EN_NUM = ["(A)", "(B)", "(C)", "(D)", "(E)"]


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    try:
        from docx import Document  # type: ignore
        from docx.enum.text import WD_BREAK  # type: ignore
    except ImportError:
        print("python-docx 미설치: pip install python-docx", file=sys.stderr)
        return 1

    exam = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    nums = KO_NUM if exam["language"] == "ko" else EN_NUM
    doc = Document(str(TEMPLATE)) if TEMPLATE.exists() else Document()

    # 문제지
    doc.add_heading(exam["title"], level=1)
    for it in exam["items"]:
        doc.add_paragraph(f"{it['id']}. {it['stem']}  [{it['points']}점]" if exam["language"] == "ko"
                          else f"{it['id']}. {it['stem']}  [{it['points']} pts]")
        if it.get("passage"):
            p = doc.add_paragraph(it["passage"])
            p.paragraph_format.left_indent = p.paragraph_format.left_indent or 0
        if it.get("options"):
            for i, o in enumerate(it["options"]):
                doc.add_paragraph(f"{nums[i]} {o}")
        if it.get("vocab_entries"):
            t = doc.add_table(rows=1, cols=4)
            t.style = "Table Grid"
            hdr = t.rows[0].cells
            for c, h in zip(hdr, ["단어", "품사", "뜻", "예문"] if exam["language"] == "ko"
                            else ["Word", "POS", "Meaning", "Example"]):
                c.text = h
            for e in it["vocab_entries"]:
                row = t.add_row().cells
                row[0].text, row[1].text = e["word"], e.get("pos", "")
                row[2].text = e.get("meaning_ko") or e.get("meaning_en", "")
                row[3].text = e["example"]
        doc.add_paragraph("")

    # 정답 및 해설 (새 페이지)
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
    doc.add_heading(("정답 및 해설" if exam["language"] == "ko" else "Answer Key") + f" — {exam['title']}", level=1)
    for it in exam["items"]:
        ans = it["answer"]
        if isinstance(ans, int) and it.get("options"):
            ans_txt = nums[ans]
        else:
            ans_txt = str(ans)
        doc.add_paragraph(f"{it['id']}. {ans_txt}")
        doc.add_paragraph(it["explanation"])
        for note in it.get("distractor_notes", []):
            doc.add_paragraph(note, style="List Bullet")

    out = Path(sys.argv[2])
    doc.save(str(out))
    print(f"저장: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
