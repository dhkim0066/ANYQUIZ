#!/usr/bin/env python3
"""텍스트 PDF에서 본문을 추출합니다.

사용법:
    python3 extract.py input.pdf [output.txt] [--no-columns]

- 2단 편집을 감지하면 왼쪽 단을 끝까지 읽은 뒤 오른쪽 단을 읽습니다. 감지한 쪽은 stderr에 알립니다.
  감지 기준: 쪽 가운데에 세로 구분선이 있거나, 가운데에 글자가 없는 세로 띠가 쪽 높이의 절반 이상 이어짐.
  단 위쪽의 머리글·배점표처럼 쪽 전체 폭을 쓰는 부분은 먼저 그대로 읽습니다.
- 잘못 감지되면(가운데가 빈 큰 표 등) --no-columns로 끕니다. 3단 이상은 지원하지 않습니다.
- 출력 텍스트가 거의 없으면(페이지당 20단어 미만) 스캔 PDF로 보고 경고와 함께 종료 코드 2를 반환합니다.
- pdfplumber가 없으면 pypdf로 대체합니다. 이 경우 2단 처리는 하지 않습니다.
"""
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8")

MIN_WORDS_PER_PAGE = 20
CENTER_BAND = (0.35, 0.65)   # 단 구분을 찾는 가로 범위 (쪽 폭 대비)
MIN_COLUMN_HEIGHT = 0.5      # 단 구간의 최소 높이 (쪽 높이 대비)
STRIP_HALF_WIDTH = 3         # 빈 세로 띠의 반폭 (pt)
MIN_WORDS_PER_SIDE = 20


def _gutter_from_rule(page):
    """쪽 가운데의 세로 구분선을 찾는다. (x, top, bottom) 또는 None."""
    lo, hi = page.width * CENTER_BAND[0], page.width * CENTER_BAND[1]
    best = None
    for o in list(page.lines) + list(page.rects):
        w, h = o["x1"] - o["x0"], o["bottom"] - o["top"]
        x = (o["x0"] + o["x1"]) / 2
        if w <= 2 and lo <= x <= hi and h >= page.height * MIN_COLUMN_HEIGHT:
            if best is None or h > best[2] - best[1]:
                best = (x, o["top"], o["bottom"])
    return best


def _gutter_from_whitespace(page, words):
    """가운데에 글자가 없는 세로 띠가 가장 길게 이어지는 곳을 찾는다."""
    lo, hi = page.width * CENTER_BAND[0], page.width * CENTER_BAND[1]
    if not words:
        return None
    text_top = min(w["top"] for w in words)
    text_bottom = max(w["bottom"] for w in words)
    best = None
    x = lo
    while x <= hi:
        blockers = sorted(
            (w["top"], w["bottom"]) for w in words
            if w["x0"] < x + STRIP_HALF_WIDTH and w["x1"] > x - STRIP_HALF_WIDTH
        )
        edges = [text_top] + [v for b in blockers for v in b] + [text_bottom]
        # 막는 낱말들 사이의 빈 구간: (시작, 끝) 쌍
        for i in range(0, len(edges) - 1, 2):
            top, bottom = edges[i], edges[i + 1]
            if bottom - top < page.height * MIN_COLUMN_HEIGHT:
                continue
            inside = [w for w in words if w["top"] >= top - 1 and w["bottom"] <= bottom + 1]
            left = [w for w in inside if w["x1"] <= x]
            right = [w for w in inside if w["x0"] >= x]
            if len(left) < MIN_WORDS_PER_SIDE or len(right) < MIN_WORDS_PER_SIDE:
                continue
            if best is None or bottom - top > best[2] - best[1]:
                best = (x, top, bottom)
        x += 2
    return best


def _page_text(page, use_columns: bool) -> tuple[str, bool]:
    """한 쪽의 텍스트와, 2단으로 처리했는지 여부."""
    if not use_columns:
        return page.extract_text() or "", False
    words = page.extract_words()
    gutter = _gutter_from_rule(page)
    if gutter:
        # 구분선이 있어도 양쪽에 글이 충분해야 단으로 본다 (표의 세로 테두리 오인 방지)
        x, top, bottom = gutter
        inside = [w for w in words if w["top"] >= top - 1 and w["bottom"] <= bottom + 1]
        if (sum(w["x1"] <= x for w in inside) < MIN_WORDS_PER_SIDE
                or sum(w["x0"] >= x for w in inside) < MIN_WORDS_PER_SIDE):
            gutter = None
    if not gutter:
        gutter = _gutter_from_whitespace(page, words)
    if not gutter:
        return page.extract_text() or "", False

    x, top, bottom = gutter
    top = max(0, top - 1)
    bottom = min(page.height, bottom + 1)
    parts = []
    regions = [
        (0, 0, page.width, top),            # 단 위쪽: 쪽 전체 폭
        (0, top, x, bottom),                # 왼쪽 단
        (x, top, page.width, bottom),       # 오른쪽 단
        (0, bottom, page.width, page.height),  # 단 아래쪽
    ]
    for box in regions:
        if box[3] - box[1] < 1 or box[2] - box[0] < 1:
            continue
        t = page.crop(box).extract_text() or ""
        if t.strip():
            parts.append(t.strip())
    return "\n".join(parts), True


def extract_with_pdfplumber(path: Path, use_columns: bool) -> tuple[list[str], list[int]]:
    import pdfplumber  # type: ignore

    pages, two_col = [], []
    with pdfplumber.open(str(path)) as pdf:
        for i, page in enumerate(pdf.pages, 1):
            text, split = _page_text(page, use_columns)
            pages.append(text)
            if split:
                two_col.append(i)
    return pages, two_col


def extract_with_pypdf(path: Path) -> list[str]:
    from pypdf import PdfReader  # type: ignore

    reader = PdfReader(str(path))
    return [(p.extract_text() or "") for p in reader.pages]


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    use_columns = "--no-columns" not in sys.argv
    if not args or "-h" in sys.argv or "--help" in sys.argv:
        print(__doc__)
        return 0 if ("-h" in sys.argv or "--help" in sys.argv) else 1
    src = Path(args[0])
    if not src.exists():
        print(f"파일 없음: {src}", file=sys.stderr)
        return 1

    two_col: list[int] = []
    try:
        pages, two_col = extract_with_pdfplumber(src, use_columns)
    except ImportError:
        pages = extract_with_pypdf(src)
        print("참고: pdfplumber가 없어 pypdf로 추출했습니다. 2단 편집이면 순서가 섞일 수 있습니다.", file=sys.stderr)

    text = "\n\n".join(f"--- page {i + 1} ---\n{t.strip()}" for i, t in enumerate(pages))
    total_words = sum(len(t.split()) for t in pages)
    per_page = total_words / max(len(pages), 1)

    if len(args) >= 2:
        Path(args[1]).write_text(text, encoding="utf-8")
        print(f"저장: {args[1]} ({len(pages)}쪽, {total_words}단어)")
    else:
        print(text)

    if two_col:
        print(f"2단 편집 감지: {', '.join(map(str, two_col))}쪽. 왼쪽 단 → 오른쪽 단 순서로 읽었습니다. "
              "순서가 이상하면 --no-columns로 다시 추출하세요.", file=sys.stderr)

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
