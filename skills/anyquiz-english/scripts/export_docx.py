#!/usr/bin/env python3
"""exam.json(v2)을 DOCX 문제지(+ 정답·해설 쪽)로 내보냅니다.

사용법:
    python3 export_docx.py generated.json out.docx [--paper-only]

같은 폴더의 render_md.py가 만든 블록 목록을 그대로 씁니다. 그래서 마크다운과 DOCX의 내용·순서가 같습니다.
assets/exam-template.docx가 있으면 그 스타일을 쓰고, 없으면 기본 문서로 만듭니다.
python-docx가 필요합니다: pip install python-docx
"""
import importlib.util
import json
import re
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8")

HERE = Path(__file__).parent
TEMPLATE = HERE.parent / "assets" / "exam-template.docx"


def load_renderer():
    """-I로 실행하면 같은 폴더 import가 안 되므로 경로로 불러온다."""
    spec = importlib.util.spec_from_file_location("render_md", HERE / "render_md.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def add_runs(par, text: str, bold_all: bool = False, italic: bool = False) -> None:
    """**굵게** 표시를 실제 굵은 글씨로 바꿔 넣는다."""
    for i, part in enumerate(re.split(r"\*\*(.+?)\*\*", text)):
        if not part:
            continue
        run = par.add_run(part)
        run.bold = bold_all or i % 2 == 1
        run.italic = italic


def main() -> int:
    flags = [a for a in sys.argv[1:] if a.startswith("-")]
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if len(args) < 2 or "-h" in flags or "--help" in flags:
        print(__doc__)
        return 0 if flags and len(args) < 2 else 1
    try:
        from docx import Document  # type: ignore
        from docx.enum.text import WD_BREAK  # type: ignore
        from docx.shared import Cm  # type: ignore
    except ImportError:
        print("python-docx 미설치: pip install python-docx", file=sys.stderr)
        return 1
    try:
        exam = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"읽을 수 없음: {args[0]}: {e}", file=sys.stderr)
        return 1
    if exam.get("schema_version") != 2:
        print("schema_version 2가 아닙니다. references/schema.md를 따라 다시 작성하세요.", file=sys.stderr)
        return 1

    blocks = load_renderer().build_blocks(exam, paper_only="--paper-only" in flags)
    doc = Document(str(TEMPLATE)) if TEMPLATE.exists() else Document()

    for b in blocks:
        k = b["k"]
        if k == "title":
            doc.add_heading(b["t"], level=1)
        elif k == "section":
            doc.add_heading(b["t"], level=2)
        elif k in ("strong", "stem"):
            add_runs(doc.add_paragraph(), b["t"], bold_all=True)
        elif k == "p":
            add_runs(doc.add_paragraph(), b["t"])
        elif k == "note":
            add_runs(doc.add_paragraph(), b["t"].strip("*"), italic=True)
        elif k == "quote":
            par = doc.add_paragraph()
            par.paragraph_format.left_indent = Cm(0.8)
            add_runs(par, b["t"])
        elif k == "opts":
            if b["inline"]:
                doc.add_paragraph("　".join(b["items"]))
            else:
                for x in b["items"]:
                    doc.add_paragraph(x)
        elif k == "table":
            t = doc.add_table(rows=1, cols=len(b["head"]))
            t.style = "Table Grid"
            for cell, h in zip(t.rows[0].cells, b["head"]):
                add_runs(cell.paragraphs[0], str(h), bold_all=True)
            for r in b["rows"]:
                for cell, v in zip(t.add_row().cells, r):
                    add_runs(cell.paragraphs[0], str(v))
            doc.add_paragraph("")
        elif k == "bullets":
            for x in b["items"]:
                doc.add_paragraph(x, style="List Bullet")
        elif k == "break":
            doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
        # rule: DOCX에서는 생략

    out = Path(args[1])
    doc.save(str(out))
    print(f"저장: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
