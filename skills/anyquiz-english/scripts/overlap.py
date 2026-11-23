#!/usr/bin/env python3
"""생성된 지문·예문이 원본 텍스트를 얼마나 베꼈는지 n-gram 중복률로 측정합니다.

사용법:
    python3 overlap.py source.txt generated.json [--n 6] [--threshold 0.15]
    python3 overlap.py other-run.json generated.json      # 다른 실행의 생성물과 비교

첫 인자가 원본 텍스트(.txt, .md)면 "원본을 베꼈는가"를, 다른 실행의 생성물(.json)이면
"실행끼리 같은 글이 나오는가"를 잽니다. 출력의 (N n-gram)은 겹친 여섯 낱말 묶음의 개수입니다.

측정 방법:
  생성물의 각 텍스트(지문, 주어진 글, 요약문, 보기, 단어집 예문, 짝짓기 뜻풀이)를 단어 n-gram(기본 6)으로
  쪼개고, 원본에 그대로 등장하는 n-gram의 비율을 계산합니다. 문항별로 출력하고,
  임계값(기본 15%)을 넘는 문항이 하나라도 있으면 종료 코드 1.
  순서·삽입·무관한 문장의 보기는 기호뿐이라 세지 않습니다(원본과 같을 수밖에 없음).

passage 모드에서는 지문을 그대로 쓰는 것이 정상이므로 이 스크립트를 돌리지 않습니다.
"""
import json
import re
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8")

SYMBOL_OPTIONS = {"order", "insertion", "irrelevant"}


def tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", text.lower())


def ngrams(toks: list[str], n: int) -> set[tuple[str, ...]]:
    return {tuple(toks[i : i + n]) for i in range(max(len(toks) - n + 1, 0))}


def ratio(text: str, src_grams: set, n: int) -> tuple[float, int]:
    g = ngrams(tokens(text), n)
    if not g:
        return 0.0, 0
    hit = len(g & src_grams)
    return hit / len(g), hit


def item_text(it: dict) -> str:
    parts: list[str] = [it.get(k, "") for k in ("given", "passage", "prompt_text")]
    if it.get("subtype") not in SYMBOL_OPTIONS:
        parts += it.get("options") or []
    parts += [e.get("example", "") for e in it.get("vocab_entries", [])]
    parts += it.get("match_right") or []
    return " ".join(parts)


def main() -> int:
    args = sys.argv[1:]
    if len(args) < 2 or args[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if args and args[0] in ("-h", "--help") else 1
    n, threshold = 6, 0.15
    if "--n" in args:
        n = int(args[args.index("--n") + 1])
    if "--threshold" in args:
        threshold = float(args[args.index("--threshold") + 1])

    src_text = Path(args[0]).read_text(encoding="utf-8")
    if args[0].lower().endswith(".json"):
        src_text = " \n ".join(item_text(it) for it in json.loads(src_text)["items"])
    src_grams = ngrams(tokens(src_text), n)
    exam = json.loads(Path(args[1]).read_text(encoding="utf-8"))

    failed = 0
    for it in exam["items"]:
        text = item_text(it)
        r, hit = ratio(text, src_grams, n)
        flag = "FAIL" if r > threshold else "ok"
        if r > threshold:
            failed += 1
        print(f"item {it['id']:>3} {flag:>4}  중복 {r:6.1%}  ({hit} n-gram)")
    print(f"\n임계값 {threshold:.0%}, n={n}, 초과 문항 {failed}개")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
