#!/usr/bin/env python3
"""텍스트 PDF에서 본문을 추출합니다.

사용법:
    python3 extract.py input.pdf [output.txt]

출력 텍스트가 거의 없으면(페이지당 20단어 미만) 스캔 PDF로 보고 경고와 함께 종료 코드 2를 반환합니다.
pdfplumber가 없으면 pypdf로 대체합니다.
"""
import sys
from pathlib import Path

MIN_WORDS_PER_PAGE = 20


def extract_with_pdfplumber(path: Path) -> list[str]:
    import pdfplumber  # type: ignore

    pages = []
    with pdfplumber.open(str(path)) as pdf:
        for page in pdf.pages:
            pages.append(page.extract_text() or "")
    return pages


def extract_with_pypdf(path: Path) -> list[str]:
    from pypdf import PdfReader  # type: ignore

    reader = PdfReader(str(path))
    return [(p.extract_text() or "") for p in reader.pages]


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    src = Path(sys.argv[1])
    if not src.exists():
        print(f"파일 없음: {src}", file=sys.stderr)
        return 1

    try:
        pages = extract_with_pdfplumber(src)
    except ImportError:
        pages = extract_with_pypdf(src)

    text = "\n\n".join(f"--- page {i + 1} ---\n{t.strip()}" for i, t in enumerate(pages))
    total_words = sum(len(t.split()) for t in pages)
    per_page = total_words / max(len(pages), 1)

    if len(sys.argv) >= 3:
        Path(sys.argv[2]).write_text(text, encoding="utf-8")
        print(f"저장: {sys.argv[2]} ({len(pages)}쪽, {total_words}단어)")
    else:
        print(text)

    if per_page < MIN_WORDS_PER_PAGE:
        print(
            f"\n경고: 페이지당 평균 {per_page:.0f}단어. 스캔 이미지 PDF로 보입니다. "
            "이 스킬은 텍스트 PDF만 지원합니다.",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
