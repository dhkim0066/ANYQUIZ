#!/usr/bin/env python3
"""exam.json을 스키마와 작성 규칙으로 검사합니다.

사용법:
    python3 validate_schema.py generated.json
    python3 validate_schema.py --compare source.json generated.json

검사 항목:
  1. JSON Schema (exam.schema.json)
  2. 작성 규칙: 보기 수와 distractor_notes 수, 보기 길이 균형(정답만 길거나 짧은 경우 포함), 정답 분포,
     답 인덱스 범위, 지문 단어 수 일치, 지문 묶음(passage_group) 일관성
  3. --compare: 원본과 생성 결과의 형식 일치 (schema.md의 "비슷함" 표). 보기 표기·발문 언어·지문 묶음 구조 포함

종료 코드: 0 통과, 1 실패. 실패 항목은 한 줄씩 출력합니다.
"""
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]


def load(p: str) -> dict:
    return json.loads(Path(p).read_text(encoding="utf-8"))


def schema_errors(exam: dict) -> list[str]:
    try:
        import jsonschema  # type: ignore
    except ImportError:
        return ["jsonschema 미설치: pip install jsonschema"]
    schema = json.loads((HERE / "exam.schema.json").read_text(encoding="utf-8"))
    v = jsonschema.Draft202012Validator(schema)
    return [f"schema: {'/'.join(str(x) for x in e.path)}: {e.message}" for e in v.iter_errors(exam)]


def rule_errors(exam: dict) -> list[str]:
    errs: list[str] = []
    answers = Counter()
    mc_count = 0
    for it in exam["items"]:
        tag = f"item {it['id']}"
        opts = it.get("options")
        if opts:
            mc_count += 1
            if isinstance(it["answer"], int):
                if not 0 <= it["answer"] < len(opts):
                    errs.append(f"{tag}: answer 인덱스 {it['answer']}가 보기 범위 밖")
                else:
                    answers[it["answer"]] += 1
            else:
                errs.append(f"{tag}: 객관식인데 answer가 정수가 아님")
            notes = it.get("distractor_notes") or []
            if it["type"] == "reading" and len(notes) != len(opts) - 1:
                errs.append(f"{tag}: distractor_notes {len(notes)}개, 보기 수-1={len(opts) - 1}개여야 함")
            lens = [len(o.split()) for o in opts]
            if max(lens) > 2 * max(min(lens), 1) and max(lens) - min(lens) >= 3:
                errs.append(f"{tag}: 보기 길이 불균형 (단어 수 {lens})")
            # 정답만 혼자 길거나 짧은 경우 (round-00 02-05: 정답 10단어, 나머지 6~7단어)
            if isinstance(it["answer"], int) and 0 <= it["answer"] < len(opts):
                a_len = lens[it["answer"]]
                others = [n for i, n in enumerate(lens) if i != it["answer"]]
                if a_len - max(others) >= 3:
                    errs.append(f"{tag}: 정답 보기만 김 (정답 {a_len}단어, 나머지 최대 {max(others)}단어). 길이가 단서가 됨")
                elif min(others) - a_len >= 3:
                    errs.append(f"{tag}: 정답 보기만 짧음 (정답 {a_len}단어, 나머지 최소 {min(others)}단어). 길이가 단서가 됨")
        if it.get("passage") is not None:
            actual = len(it["passage"].split())
            declared = it.get("passage_words", actual)
            if abs(actual - declared) > max(5, actual * 0.1):
                errs.append(f"{tag}: passage_words={declared}, 실제 {actual}")
        if it["type"] == "cloze" and it.get("passage") and "____" not in it["passage"] and "(A)" not in it["passage"]:
            errs.append(f"{tag}: cloze 지문에 빈칸 표시(____ 또는 (A))가 없음")
        if it["type"] == "vocab" and it["subtype"] == "word-list":
            for e in it.get("vocab_entries", []):
                if len(e["example"].split()) < 6:
                    errs.append(f"{tag}: '{e['word']}' 예문이 너무 짧음")
    # 지문 묶음: 같은 passage_group은 지문이 완전히 같고 번호가 이어져야 한다
    groups: dict[str, list[dict]] = {}
    for it in exam["items"]:
        if it.get("passage_group"):
            groups.setdefault(it["passage_group"], []).append(it)
    for g, members in groups.items():
        if len({m.get("passage") for m in members}) > 1:
            errs.append(f"passage_group {g}: 문항 {[m['id'] for m in members]}의 지문이 서로 다름")
        ids = [m["id"] for m in members]
        if ids != list(range(ids[0], ids[0] + len(ids))):
            errs.append(f"passage_group {g}: 문항 번호가 이어지지 않음 {ids}")
    if mc_count >= 5 and answers:
        top, n = answers.most_common(1)[0]
        if n / mc_count > 0.4:
            errs.append(f"정답 분포: 보기 {top}이 {n}/{mc_count} ({n / mc_count:.0%}). 40% 초과")
    return errs


def compare_errors(src: dict, gen: dict) -> list[str]:
    errs: list[str] = []
    if src.get("option_marker") != gen.get("option_marker"):
        errs.append(f"보기 표기: 원본 {src.get('option_marker')}, 생성 {gen.get('option_marker')}")
    if src.get("language") != gen.get("language"):
        errs.append(f"발문 언어: 원본 {src.get('language')}, 생성 {gen.get('language')}")

    def partition(exam: dict) -> list[list[int]]:
        g: dict[str, list[int]] = {}
        for it in exam["items"]:
            if it.get("passage_group"):
                g.setdefault(it["passage_group"], []).append(it["id"])
        return sorted(g.values())

    if partition(src) != partition(gen):
        errs.append(f"지문 묶음 구조: 원본 {partition(src)}, 생성 {partition(gen)}")
    if len(src["items"]) != len(gen["items"]):
        errs.append(f"문항 수: 원본 {len(src['items'])}, 생성 {len(gen['items'])}")
        return errs
    for a, b in zip(src["items"], gen["items"]):
        tag = f"item {a['id']}"
        if (a["type"], a["subtype"]) != (b["type"], b["subtype"]):
            errs.append(f"{tag}: 유형 {a['type']}/{a['subtype']} → {b['type']}/{b['subtype']}")
        if len(a.get("options") or []) != len(b.get("options") or []):
            errs.append(f"{tag}: 보기 수 {len(a.get('options') or [])} → {len(b.get('options') or [])}")
        if a["points"] != b["points"]:
            errs.append(f"{tag}: 배점 {a['points']} → {b['points']}")
        if abs(LEVELS.index(a["level"]) - LEVELS.index(b["level"])) > 1:
            errs.append(f"{tag}: 수준 {a['level']} → {b['level']} (한 단계 초과)")
        pw_a, pw_b = a.get("passage_words"), b.get("passage_words")
        if pw_a and pw_b and abs(pw_b - pw_a) > pw_a * 0.2:
            errs.append(f"{tag}: 지문 길이 {pw_a} → {pw_b} (±20% 초과)")
        if not set(a["topic_tags"]) & set(b["topic_tags"]):
            errs.append(f"{tag}: 소재 태그 겹침 없음 {a['topic_tags']} vs {b['topic_tags']} (사용자가 다른 소재를 요청했다면 무시)")
    return errs


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 1
    errs: list[str] = []
    if args[0] == "--compare":
        src, gen = load(args[1]), load(args[2])
        errs += schema_errors(gen) + rule_errors(gen) + compare_errors(src, gen)
    else:
        gen = load(args[0])
        errs += schema_errors(gen) + rule_errors(gen)
    if errs:
        print(f"실패 {len(errs)}건")
        for e in errs:
            print(" -", e)
        return 1
    print("통과")
    return 0


if __name__ == "__main__":
    sys.exit(main())
