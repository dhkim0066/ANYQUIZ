#!/usr/bin/env python3
"""새 지문의 겉모습(이름, 장소, 사물, 전개 방식)을 무작위로 뽑습니다.

    python3 pick_seeds.py 8              # 지문 8개에 쓸 조합
    python3 pick_seeds.py 8 --seed 4127  # 같은 조합을 다시 뽑기

같은 원본으로 여러 번 만들면 모델이 고르는 이름과 장면이 비슷해집니다. 고르는 일을
모델에게 맡기지 않고 여기서 뽑습니다. 소재(topic_tags)는 원본을 따르고, 여기서 뽑은 것은
그 소재를 풀어내는 겉모습에만 씁니다. 지문 성격에 맞지 않는 칸은 버려도 됩니다
(설명문에는 이름·장소를 쓰지 않고 전개 방식만 쓰는 식).

출력 첫 줄의 seed를 기록해 두면 같은 조합을 다시 만들 수 있습니다.
"""
from __future__ import annotations

import random
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# 이름만 씁니다. 성을 붙이지 않고 실존 인물을 가리키지 않습니다.
NAMES = [
    "Aiko", "Amara", "Anders", "Bao", "Callum", "Carmen", "Dalia", "Daniel", "Elif", "Emeka",
    "Farah", "Felix", "Greta", "Hana", "Hugo", "Imani", "Ines", "Jonas", "Jun", "Kavya",
    "Kofi", "Lena", "Leo", "Luca", "Malik", "Mateo", "Mei", "Nadia", "Nico", "Noor",
    "Olga", "Omar", "Paula", "Priya", "Quinn", "Rafael", "Rosa", "Sana", "Selim", "Tae",
    "Tomas", "Uma", "Vera", "Viktor", "Wren", "Yara", "Yusuf", "Zoe",
]
SETTINGS = [
    "동네 빵집", "버스 정류장", "학교 옥상 텃밭", "바닷가 마을", "산속 작은 역", "주말 벼룩시장",
    "오래된 도서관", "아파트 옥상", "강변 자전거길", "시골 우체국", "수영장 탈의실", "기차 식당칸",
    "학교 과학실", "동네 세탁소", "공항 대기실", "작은 섬의 선착장", "야시장", "박물관 뒤뜰",
    "농구장 옆 벤치", "할머니 댁 부엌", "캠핑장", "꽃집", "자전거 수리점", "동물 보호소",
    "지역 라디오 방송국", "눈 오는 날 운동장", "지하철 환승 통로", "항구의 어시장", "과수원", "천문대",
]
OBJECTS = [
    "낡은 우산", "빨간 보온병", "고장 난 손목시계", "종이 지도", "화분 하나", "필름 카메라",
    "손으로 쓴 쪽지", "한 짝뿐인 장갑", "연필 깎는 칼", "중고 기타", "열쇠 꾸러미", "유리병",
    "접이식 의자", "오래된 요리책", "나침반", "털실 뭉치", "손전등", "자전거 벨",
    "도시락 통", "우표 한 장", "체스 말", "씨앗 봉지", "작은 종", "물감 상자",
    "버스 승차권", "망원경", "빈 새장", "라디오", "돋보기", "양초",
]
ANGLES_STORY = [
    "처음 해 보는 일", "계획과 다르게 흘러간 하루", "잃어버린 것을 찾기", "작은 실수에서 배운 것",
    "낯선 사람의 도움", "오래 미뤄 둔 일을 끝내기", "약속 시간에 쫓기기", "둘이 생각이 달라 생긴 일",
    "기다림 끝의 뜻밖의 결과", "누군가에게 몰래 준비한 것", "익숙한 곳을 새로 보게 된 일", "포기하려다 다시 해 본 일",
]
ANGLES_EXPOSITORY = [
    "흔한 생각 → 그와 다른 사실", "관찰한 사례 → 일반적인 결론", "문제 → 원인 → 해결",
    "옛 방식과 지금 방식 비교", "뜻 설명 → 예시 둘", "장점 하나와 단점 하나",
    "질문으로 시작해 답으로 끝내기", "과정을 순서대로", "두 대상의 공통점과 차이점", "예상 밖의 결과와 그 이유",
]


def main() -> int:
    args = sys.argv[1:]
    if not args or "-h" in args or "--help" in args:
        print(__doc__)
        return 0 if args else 2
    seed = None
    if "--seed" in args:
        i = args.index("--seed")
        try:
            seed = int(args[i + 1])
        except (IndexError, ValueError):
            print("--seed 뒤에 정수를 적어 주세요.", file=sys.stderr)
            return 2
        del args[i:i + 2]
    try:
        n = int(args[0])
    except (IndexError, ValueError):
        print("지문 개수를 정수로 적어 주세요. 예: pick_seeds.py 8", file=sys.stderr)
        return 2
    if not 1 <= n <= 60:
        print("지문 개수는 1~60 사이여야 합니다.", file=sys.stderr)
        return 2
    if seed is None:
        seed = random.SystemRandom().randrange(1, 10 ** 6)
    rng = random.Random(seed)

    def spread(pool: list[str], k: int) -> list[str]:
        """k개를 뽑되, 풀을 다 쓰기 전에는 같은 것을 다시 뽑지 않는다."""
        out: list[str] = []
        while len(out) < k:
            out += rng.sample(pool, min(len(pool), k - len(out)))
        return out

    names = spread(NAMES, n * 2)
    cols = [spread(SETTINGS, n), spread(OBJECTS, n), spread(ANGLES_STORY, n), spread(ANGLES_EXPOSITORY, n)]
    print(f"seed {seed}  (다시 뽑으려면 --seed {seed})")
    print("| 지문 | 이름 | 장소 | 사물 | 이야기 전개 | 설명문 전개 |")
    print("|---|---|---|---|---|---|")
    for i in range(n):
        print(f"| {i + 1} | {names[2 * i]}, {names[2 * i + 1]} | " + " | ".join(c[i] for c in cols) + " |")
    print("\n소재(topic_tags)는 원본을 따릅니다. 위 조합은 겉모습에만 쓰고, 지문 성격에 맞지 않는 칸은 버립니다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
