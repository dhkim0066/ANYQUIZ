#!/usr/bin/env python3
"""새 지문에 쓸 인물 이름을 무작위로 뽑습니다.

    python3 pick_names.py 8                       # 이름 8개
    python3 pick_names.py 8 --avoid source.txt    # 원본에 나온 이름은 빼고
    python3 pick_names.py 8 --seed 4127           # 같은 이름을 다시 뽑기

같은 원본으로 여러 번 만들면 모델이 고르는 이름이 비슷해집니다. 이름 고르기를 모델에게
맡기지 않고 여기서 뽑습니다. 첫 인자는 **필요한 이름의 수**입니다(지문 수가 아닙니다).
인물이 나오지 않는 설명문에는 쓰지 않아도 됩니다. 뽑힌 순서대로 지문에 배정합니다.

이 스크립트는 이름만 바꿉니다. 지문의 사건과 결론을 원본과 다르게 쓰는 일은
references/subject-english.md 2절을 따릅니다.

출력 첫 줄의 seed를 기록해 두면 같은 이름을 다시 뽑을 수 있습니다.
"""
from __future__ import annotations

import random
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# 이름만 씁니다. 성을 붙이지 않고 실존 인물을 가리키지 않습니다.
NAMES = [
    "Aiko", "Alma", "Amara", "Anders", "Anika", "Arjun", "Bao", "Bruno", "Callum", "Carmen",
    "Chidi", "Clara", "Dalia", "Daniel", "Davi", "Elif", "Emeka", "Esther", "Farah", "Felix",
    "Freya", "Gael", "Greta", "Hana", "Hugo", "Ibrahim", "Imani", "Ines", "Ivan", "Jonas",
    "Jun", "Kavya", "Kenji", "Kofi", "Lena", "Leo", "Lior", "Luca", "Malik", "Marta",
    "Mateo", "Mei", "Mina", "Nadia", "Nico", "Noor", "Oksana", "Olga", "Omar", "Paula",
    "Pedro", "Priya", "Quinn", "Rafael", "Rosa", "Ryo", "Sana", "Selim", "Sofia", "Soren",
    "Tae", "Tariq", "Tomas", "Uma", "Valentina", "Vera", "Viktor", "Wanjiru", "Wren", "Yara",
    "Yusuf", "Zainab", "Zoe", "Zuri",
]


def main() -> int:
    args = sys.argv[1:]
    if not args or "-h" in args or "--help" in args:
        print(__doc__)
        return 0 if args else 2
    seed, avoid = None, ""
    for flag in ("--seed", "--avoid"):
        if flag in args:
            i = args.index(flag)
            if i + 1 >= len(args):
                print(f"{flag} 뒤에 값을 적어 주세요.", file=sys.stderr)
                return 2
            val = args[i + 1]
            del args[i:i + 2]
            if flag == "--seed":
                try:
                    seed = int(val)
                except ValueError:
                    print("--seed 뒤에 정수를 적어 주세요.", file=sys.stderr)
                    return 2
            else:
                try:
                    avoid = Path(val).read_text(encoding="utf-8")
                except (FileNotFoundError, UnicodeDecodeError) as e:
                    print(f"읽을 수 없음: {val}: {e}", file=sys.stderr)
                    return 2
    try:
        n = int(args[0])
    except (IndexError, ValueError):
        print("필요한 이름의 수를 정수로 적어 주세요. 예: pick_names.py 8", file=sys.stderr)
        return 2
    seen = {w.lower() for w in re.findall(r"[A-Za-z]+", avoid)}
    pool = [x for x in NAMES if x.lower() not in seen]
    if not 1 <= n <= len(pool):
        print(f"이름의 수는 1~{len(pool)} 사이여야 합니다.", file=sys.stderr)
        return 2
    if seed is None:
        seed = random.SystemRandom().randrange(1, 10 ** 6)
    names = random.Random(seed).sample(pool, n)
    print(f"seed {seed}  (다시 뽑으려면 --seed {seed}" + (", 같은 --avoid 파일과 함께" if avoid else "") + ")")
    print(", ".join(names))
    if avoid:
        skipped = [x for x in NAMES if x.lower() in seen]
        if skipped:
            print(f"원본에 나와서 뺀 이름: {', '.join(skipped)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
