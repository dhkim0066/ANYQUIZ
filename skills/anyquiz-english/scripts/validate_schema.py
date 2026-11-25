#!/usr/bin/env python3
"""exam.json(v2)을 검사합니다.

사용법:
    python3 validate_schema.py file.json
    python3 validate_schema.py --compare source.json generated.json
    python3 validate_schema.py --stats file.json
    python3 validate_schema.py --words-in input.txt generated.json

file.json 하나만 주면 그 파일의 role에 맞춰 검사합니다.
  - role: source     구조와 유형별 담는 법만 검사합니다. 작성 규칙은 적용하지 않습니다(원본은 고칠 수 없는 기준).
  - role: generated  위에 더해 정답·해설·오답 이유의 존재와 작성 규칙(보기 길이, 정답 분포 등)을 검사합니다.

--compare  두 파일을 각각 검사한 뒤, 형식이 같은지 비교합니다 (schema.md "원본과 생성물의 형식 비교").
--stats    지문 단어 수, 문단 수, 문장 평균 길이, 보기 낱말 수를 문항별로 출력합니다. JSON에 적지 않고 여기서 봅니다.
           구조 검사를 하지 않으므로 수준(level)을 아직 정하지 않은 파일에도 쓸 수 있습니다.
           .json이 아닌 글 파일을 주면 그 글의 낱말 수와 문장 평균 길이만 냅니다(단어집 모드의 입력 글).

--words-in 입력 글에서 단어를 뽑은 단어집일 때, 표제어가 실제로 그 글에 있는지 봅니다. 못 찾은 단어는 주의로 알립니다
           (불규칙 변화형은 가려내지 못하므로 직접 확인).

종료 코드: 0 통과, 1 실패. 실패 항목은 한 줄씩 출력합니다.
"""
import json
import re
import statistics
import sys
from collections import Counter
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8")

HERE = Path(__file__).parent
LEVELS = ["A1", "A2", "A2+", "B1", "B1+", "B2", "B2+", "C1", "C2"]
WARNINGS: list[str] = []   # 실패로 세지 않고 알리기만 하는 항목

SUBTYPES = {
    "cloze": {"single-blank", "multi-blank", "word-bank"},
    "vocab": {"word-list", "meaning-write", "synonym-match", "definition-match"},
    "reading": {"main-idea", "title", "blank-inference", "detail", "reference", "implied-meaning",
                "inference", "order", "insertion", "irrelevant", "summary"},
    # 지원 유형 밖. 만들기는 하되 출력 맨 위에 따로 알린다 (작성 규칙과 유형별 검사가 없음)
    "other": {"choice", "open-response"},
}
ROWS = {"meaning-write", "synonym-match", "definition-match", "word-bank"}   # 줄마다 번호를 붙일 수 있는 유형
POSITION = {"insertion", "irrelevant"}            # 보기가 지문 안의 위치·번호 기호
COMBO = {"order", "multi-blank", "summary"}       # 보기가 조합
MATCH = {"synonym-match", "definition-match"}
NO_ANSWER = {"word-list", "meaning-write"}
NO_OPTIONS = MATCH | NO_ANSWER | {"word-bank", "open-response"}
BLANK = re.compile(r"_{3,}")
UNDERLINE = re.compile(r"(?<!_)__(?!_)(.+?)(?<!_)__(?!_)")
SAYS_UNDERLINE = re.compile(r"밑줄|underlined", re.I)
WORD = re.compile(r"[A-Za-z]+(?:['’\-][A-Za-z]+)*")
MARKER = re.compile(r"\((?:[A-Za-z]|\d{1,3})\)")
COMBO_SPLIT = re.compile(r"\s*[–—－]\s*|\s+-\s+")


def en_words(text: str) -> list[str]:
    return WORD.findall(MARKER.sub(" ", text or ""))


def passage_words(it: dict) -> int:
    return len(en_words(it.get("given", ""))) + len(en_words(it.get("passage", "")))


def opt_len(o: str) -> int:
    return len(o.split())


def sentence_lengths(it: dict) -> list[int]:
    text = " ".join(x for x in (it.get("given"), it.get("passage")) if x)
    return [len(en_words(s)) for s in re.split(r"(?<=[.!?])\s+", text) if len(en_words(s)) >= 3]


def paragraph_count(it: dict) -> int:
    return len([p for p in re.split(r"\n\s*\n", it.get("passage", "")) if p.strip()])


def row_count(it: dict) -> int:
    st = it.get("subtype")
    if st == "meaning-write":
        return len(it.get("vocab_entries", []))
    if st in MATCH:
        return len(it.get("match_left", []))
    if st == "word-bank":
        return len(BLANK.findall(it.get("passage", "")))
    return 1


def numbering(items: list[dict]) -> dict[int, tuple[int, int]]:
    """문항 id → 문제지에 찍히는 번호 (처음, 끝). render_md.py의 같은 이름 함수와 같아야 한다."""
    out: dict[int, tuple[int, int]] = {}
    n = 1
    for it in items:
        k = max(row_count(it), 1) if it.get("numbered_rows") else 1
        out[it["id"]] = (n, n + k - 1)
        n += k
    return out


def load(p: str) -> dict:
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except FileNotFoundError:
        sys.exit(f"파일 없음: {p}")
    except json.JSONDecodeError as e:
        sys.exit(f"JSON 형식 오류 ({p}): {e}")


def schema_errors(exam: dict) -> list[str]:
    try:
        import jsonschema  # type: ignore
    except ImportError:
        return ["jsonschema 미설치: pip install jsonschema"]
    schema = json.loads((HERE / "exam.schema.json").read_text(encoding="utf-8"))
    v = jsonschema.Draft202012Validator(schema)
    out = []
    for e in sorted(v.iter_errors(exam), key=lambda e: list(e.path)):
        where = "/".join(str(x) for x in e.path) or "(최상위)"
        out.append(f"schema: {where}: {e.message}")
    return out


def needs_answers(exam: dict) -> bool:
    return exam["role"] == "generated" or exam.get("answer_key") in ("provided", "solved")


def structure_errors(exam: dict) -> list[str]:
    """두 역할 모두에 적용: 유형별 담는 법."""
    errs: list[str] = []
    items = exam["items"]
    role = exam["role"]
    if role == "source" and "answer_key" not in exam:
        errs.append("source에는 answer_key(provided/solved/none)가 필요함")
    if [it["id"] for it in items] != list(range(1, len(items) + 1)):
        errs.append(f"문항 id는 1부터 순서대로여야 함: {[it['id'] for it in items]}")

    secs = exam.get("sections")
    if secs:
        expect = 1
        for s in secs:
            if s["first"] != expect or s["last"] < s["first"]:
                errs.append(f"sections: '{s['title']}'의 범위 {s['first']}~{s['last']}가 앞 영역과 이어지지 않음")
            expect = s["last"] + 1
        if expect != len(items) + 1:
            errs.append(f"sections가 문항 1~{len(items)}를 빠짐없이 덮지 않음 (마지막 {expect - 1})")

    if "review" in exam:
        if role != "generated":
            errs.append("review(검토 필요 문항)는 generated에만 씀")
        for r in exam["review"]:
            if not 1 <= r["id"] <= len(items):
                errs.append(f"review: {r['id']}번 문항이 없음")

    # 발문을 생략할 수 있는 문항: 영역 지시문이나 묶음 안내문이 발문을 대신하는 경우
    covered: set[int] = set()
    for s in secs or []:
        if s.get("instruction"):
            covered.update(range(s["first"], s["last"] + 1))
    lead = {it["passage_group"] for it in items if it.get("passage_group") and it.get("group_instruction")}
    covered.update(it["id"] for it in items if it.get("passage_group") in lead)

    group_passage = {it["passage_group"]: it.get("passage", "") for it in items if it.get("passage_group")}
    want_answer = needs_answers(exam)
    disp = numbering(items)
    for it in items:
        if SAYS_UNDERLINE.search(it.get("stem", "")):
            where = " ".join([it.get("stem", ""), it.get("passage", ""), group_passage.get(it.get("passage_group"), ""),
                              it.get("given", ""), it.get("prompt_text", ""), " ".join(it.get("options") or [])])
            if "**" in where and not UNDERLINE.search(where):
                errs.append(f"item {it['id']}: 발문은 밑줄인데 표시가 굵게(**…**)임. 밑줄 대상은 __…__로 감쌈")
        tag, st = f"item {it['id']}", it["subtype"]
        if st not in SUBTYPES[it["type"]]:
            errs.append(f"{tag}: type {it['type']}에 subtype {st}는 올 수 없음")
            continue
        opts = it.get("options")
        passage = it.get("passage", "")

        def need(field: str, why: str = "") -> bool:
            if field not in it:
                errs.append(f"{tag}: {st}에는 {field}가 필요함{(' (' + why + ')') if why else ''}")
                return False
            return True

        def forbid(field: str, why: str) -> None:
            if field in it:
                errs.append(f"{tag}: {st}에는 {field}를 쓰지 않음 ({why})")

        if it["type"] == "other":
            need("other_label", "원본 유형의 이름. 예: 어법, 서술형 영작")
        else:
            forbid("other_label", "type이 other인 문항에만 씀")
        if it.get("numbered_rows"):
            if st not in ROWS:
                errs.append(f"{tag}: numbered_rows는 뜻 쓰기·짝짓기·보기 상자(word-bank)에만 씀")
            elif st == "word-bank":
                n_par = len([p for p in re.split(r"\n\s*\n", passage) if p.strip()])
                if n_par != len(BLANK.findall(passage)):
                    errs.append(f"{tag}: numbered_rows인 word-bank는 문단 하나에 빈칸 하나 "
                                f"(문단 {n_par}, 빈칸 {len(BLANK.findall(passage))}). 번호는 적지 않음(출력할 때 붙음)")
        if "stem" not in it and it["type"] != "cloze" and st != "word-list" and it["id"] not in covered:
            errs.append(f"{tag}: stem(발문)이 없음. 생략하려면 그 영역의 sections[].instruction이나 "
                        "묶음의 group_instruction이 발문을 대신해야 함 (원본에 없는 발문을 지어 넣지 말 것)")
        if st in NO_OPTIONS:
            forbid("options", "객관식이 아님")
        else:
            need("options")
        if it["type"] == "reading" or st in ("single-blank", "multi-blank", "word-bank"):
            need("passage")
        if "polarity" in it and st != "detail":
            errs.append(f"{tag}: polarity는 detail에만 씀")
        if st == "detail":
            need("polarity", "일치하는 것이면 match, 일치하지 않는 것이면 mismatch")
        if opts and st not in POSITION and st != "order":
            need("option_language", "보기 언어 ko/en")

        if st == "order":
            # 장문 독해형: 주어진 글이 묶음 지문 안의 (A)이고 (B)(C)(D)를 배열한다. given을 따로 적지 않는다.
            in_group = bool(it.get("passage_group")) and "given" not in it and "(D)" in passage
            if not in_group:
                need("given", "주어진 글. 주어진 글이 묶음 지문의 (A)이면 지문에 (A)~(D)를 적고 given은 생략")
            for m in (("(A)", "(B)", "(C)", "(D)") if in_group else ("(A)", "(B)", "(C)")):
                if m not in passage:
                    errs.append(f"{tag}: order의 passage에 {m} 단락이 없음")
            for o in opts or []:
                if not re.fullmatch(r"\([A-Z]\)(\s*(?:-|–|—|→)\s*\([A-Z]\))+", o):
                    errs.append(f"{tag}: order 보기는 '(B)-(C)-(A)' 또는 '(B) → (C) → (A)' 형식이어야 함: {o!r}")
                elif in_group and "(A)" in o:
                    errs.append(f"{tag}: (A)가 주어진 글이면 보기에는 (B)(C)(D)만 씀: {o!r}")
        elif st == "insertion":
            need("given", "주어진 문장")
        if st in POSITION:
            for o in opts or []:
                if o not in passage:
                    errs.append(f"{tag}: {st}의 보기 {o!r}가 지문 안에 없음 (보기는 지문에 박힌 기호여야 함)")
        if st == "summary":
            if need("prompt_text", "요약문") and not BLANK.search(it["prompt_text"]):
                errs.append(f"{tag}: 요약문(prompt_text)에 빈칸(____)이 없음")
        if st == "single-blank" and passage:
            if not BLANK.search(passage):
                errs.append(f"{tag}: 지문에 빈칸(____)이 없음")
            if it.get("passage_group") and f"({disp[it['id']][0]})" not in passage:
                errs.append(f"{tag}: 묶음 지문의 빈칸에는 문항 번호를 붙임. 지문에 '({disp[it['id']][0]})'가 없음")
        if st == "multi-blank" and passage and "(A)" not in passage:
            errs.append(f"{tag}: multi-blank 지문에 (A) 자리가 없음")
        if st == "word-bank":
            need("word_bank", "보기 상자")
            n_blank = len(BLANK.findall(passage))
            if passage and n_blank == 0:
                errs.append(f"{tag}: 지문에 빈칸(____)이 없음")
            if "word_bank" in it and len(it["word_bank"]) <= n_blank:
                errs.append(f"{tag}: 보기 상자 낱말({len(it['word_bank'])})이 빈칸 수({n_blank})보다 많아야 함")
        if st in MATCH:
            forbid("vocab_entries", "문제지에 뜻이 함께 찍혀 답이 드러남. match_left/match_right를 씀")
            if need("match_left") and need("match_right"):
                L, R = it["match_left"], it["match_right"]
                if len(R) < len(L):
                    errs.append(f"{tag}: match_right({len(R)})가 match_left({len(L)})보다 짧음")
                for key, arr in (("match_left_labels", L), ("match_right_labels", R)):
                    if key in it and len(it[key]) != len(arr):
                        errs.append(f"{tag}: {key} 길이 {len(it[key])} ≠ 항목 수 {len(arr)}")
        if st == "word-list":
            if need("vocab_entries") and need("vocab_columns", "표에 나오는 열"):
                for e in it["vocab_entries"]:
                    for col in it["vocab_columns"]:
                        if not e.get(col):
                            errs.append(f"{tag}: '{e['word']}'에 {col} 열 값이 없음")
        if st == "meaning-write":
            need("vocab_entries")
            cols = it.get("vocab_columns")
            if cols is not None:
                if set(cols) - {"word", "pos", "meaning"}:
                    errs.append(f"{tag}: 뜻 쓰기의 vocab_columns는 word, pos, meaning만 씀 (품사를 문제지에 보일 때 pos를 넣음)")
                if "pos" in cols:
                    for e in it.get("vocab_entries", []):
                        if not e.get("pos"):
                            errs.append(f"{tag}: '{e['word']}'에 pos 값이 없음")
        if st not in ("word-list", "meaning-write"):
            forbid("vocab_columns", "단어집과 뜻 쓰기 전용")

        # 빈칸 문제의 분류 기준: 보기 낱말 수 중앙값
        if opts and st in ("single-blank", "blank-inference"):
            med = statistics.median(opt_len(o) for o in opts)
            if st == "single-blank" and med >= 3:
                errs.append(f"{tag}: 보기가 구·절(중앙값 {med:g}낱말)이므로 reading/blank-inference로 분류")
            if st == "blank-inference" and med <= 2:
                errs.append(f"{tag}: 보기가 단어(중앙값 {med:g}낱말)이므로 cloze/single-blank로 분류")

        # 정답의 형태
        if st in NO_ANSWER:
            continue
        if "answer" not in it:
            if want_answer:
                errs.append(f"{tag}: answer가 없음")
            continue
        a = it["answer"]
        if st == "open-response":
            if not (isinstance(a, list) and all(isinstance(x, str) for x in a)):
                errs.append(f"{tag}: 서술형의 answer는 모범 답안 문자열 배열 (하나 이상)")
        elif st == "word-bank":
            n_blank = len(BLANK.findall(passage))
            if not (isinstance(a, list) and all(isinstance(x, str) for x in a)):
                errs.append(f"{tag}: word-bank의 answer는 빈칸 순서대로 낱말 배열")
            else:
                if len(a) != n_blank:
                    errs.append(f"{tag}: answer {len(a)}개, 빈칸 {n_blank}개")
                bank = it.get("word_bank", [])
                for x in a:
                    if x not in bank:
                        errs.append(f"{tag}: 정답 '{x}'가 보기 상자에 없음")
                if len(set(a)) != len(a):
                    errs.append(f"{tag}: 같은 낱말이 정답에 두 번 나옴")
        elif st in MATCH:
            L, R = it.get("match_left", []), it.get("match_right", [])
            if not (isinstance(a, list) and all(isinstance(x, int) for x in a)):
                errs.append(f"{tag}: 짝짓기의 answer는 match_left 순서대로 match_right 인덱스 배열")
            else:
                if len(a) != len(L):
                    errs.append(f"{tag}: answer {len(a)}개, match_left {len(L)}개")
                if any(not 0 <= x < len(R) for x in a):
                    errs.append(f"{tag}: answer 인덱스가 match_right 범위를 벗어남")
                if len(set(a)) != len(a):
                    errs.append(f"{tag}: 같은 오른쪽 항목이 두 번 쓰임")
        else:
            if not isinstance(a, int):
                errs.append(f"{tag}: 객관식의 answer는 보기 인덱스(0부터)")
            elif opts and not 0 <= a < len(opts):
                errs.append(f"{tag}: answer 인덱스 {a}가 보기 범위 밖")

    # 지문 묶음
    groups: dict[str, list[dict]] = {}
    for it in items:
        if it.get("passage_group"):
            groups.setdefault(it["passage_group"], []).append(it)
    for g, members in groups.items():
        ids = [m["id"] for m in members]
        if len({m.get("passage") for m in members}) > 1:
            errs.append(f"passage_group {g}: 문항 {ids}의 지문이 서로 다름")
        if len({m.get("footnote") for m in members}) > 1:
            errs.append(f"passage_group {g}: 문항 {ids}의 각주가 서로 다름")
        if ids != list(range(ids[0], ids[0] + len(ids))):
            errs.append(f"passage_group {g}: 문항 번호가 이어지지 않음 {ids}")
        for m in members[1:]:
            if "group_instruction" in m:
                errs.append(f"item {m['id']}: group_instruction은 묶음의 첫 문항({ids[0]})에만 적음")
    for it in items:
        if "group_instruction" in it and not it.get("passage_group"):
            errs.append(f"item {it['id']}: passage_group 없이 group_instruction만 있음")
    outside = [it for it in items if it["type"] == "other"]
    if outside and role == "generated":
        nums = ", ".join(str(disp[it["id"]][0]) for it in outside)
        WARNINGS.append(f"지원 범위 밖 문항 {len(outside)}개 ({nums}번). 작성 규칙과 유형별 검사 없이 통과한 것이므로 "
                        "형식 충실도에 넣지 말고 따로 셈. 출력 맨 위에 안내가 붙음")
    return errs


def corpus_tokens(exam: dict, skip_id: int) -> set[str]:
    toks: set[str] = set()
    for it in exam["items"]:
        if it["id"] == skip_id or it["type"] == "vocab":
            continue
        parts = [it.get("passage", ""), it.get("given", ""), it.get("prompt_text", "")]
        parts += it.get("options") or []
        parts += it.get("word_bank") or []
        toks.update(w.lower() for w in en_words(" ".join(parts)))
    return toks


def in_corpus(word: str, toks: set[str], min_prefix: int = 3) -> bool:
    """낱말(또는 그 활용형)이 toks 안에 있는가. 앞부분 일치로 느슨하게 본다."""
    ws = en_words(word)
    if not ws:
        return True
    w = ws[0].lower()
    prefix = w[: max(min_prefix, len(w) - 2)]
    return any(t.startswith(prefix) for t in toks)


def writing_errors(exam: dict) -> list[str]:
    """생성물에만 적용: 정답·해설의 존재와 작성 규칙."""
    errs: list[str] = []
    answers: Counter = Counter()
    mc_count = 0
    for it in exam["items"]:
        tag, st = f"item {it['id']}", it["subtype"]
        opts = it.get("options")
        if st != "word-list" and st != "meaning-write" and not it.get("explanation"):
            errs.append(f"{tag}: explanation이 없음")
        if st == "meaning-write":
            for e in it.get("vocab_entries", []):
                if not e.get("meaning"):
                    errs.append(f"{tag}: '{e['word']}'의 정답 뜻(meaning)이 없음")
        if opts and isinstance(it.get("answer"), int) and 0 <= it["answer"] < len(opts):
            mc_count += 1
            answers[it["answer"]] += 1
            notes = it.get("distractor_notes")
            symbol_only = st in POSITION or st == "order"
            if (it["type"] == "reading" and not symbol_only) or notes is not None:
                if len(notes or []) != len(opts) - 1:
                    errs.append(f"{tag}: distractor_notes {len(notes or [])}개. 정답이 아닌 보기마다 하나씩 {len(opts) - 1}개여야 함")
            if st not in POSITION and st not in COMBO:
                lens = [opt_len(o) for o in opts]
                if max(lens) > 2 * max(min(lens), 1) and max(lens) - min(lens) >= 3:
                    errs.append(f"{tag}: 보기 길이 불균형 (낱말 수 {lens})")
                a_len = lens[it["answer"]]
                others = [n for i, n in enumerate(lens) if i != it["answer"]]
                if a_len - max(others) >= 3:
                    errs.append(f"{tag}: 정답 보기만 김 (정답 {a_len}낱말, 나머지 최대 {max(others)}낱말)")
                elif min(others) - a_len >= 3:
                    errs.append(f"{tag}: 정답 보기만 짧음 (정답 {a_len}낱말, 나머지 최소 {min(others)}낱말)")
        if st == "multi-blank" and opts:
            cols = [COMBO_SPLIT.split(o.strip()) for o in opts]
            if len({len(c) for c in cols}) != 1:
                errs.append(f"{tag}: 조합 보기의 자리 수가 서로 다름. 자리 구분은 ' – '")
            else:
                for pos in range(len(cols[0])):
                    if len({c[pos].strip().lower() for c in cols}) < 2:
                        errs.append(f"{tag}: ({chr(65 + pos)}) 자리가 모든 보기에서 같아 검사되지 않음")
        if st == "definition-match":
            L, R, a = it.get("match_left", []), it.get("match_right", []), it.get("answer")
            if isinstance(a, list) and len(a) == len(L):
                for w, idx in zip(L, a):
                    if isinstance(idx, int) and 0 <= idx < len(R):
                        ws = en_words(w)
                        if ws and in_corpus(w, {t.lower() for t in en_words(R[idx])}, min_prefix=4):
                            errs.append(f"{tag}: '{w}'의 뜻풀이에 그 낱말 자체나 파생어가 들어 있음")
        if st == "word-list" and "example" in (it.get("vocab_columns") or []):
            for e in it.get("vocab_entries", []):
                if len((e.get("example") or "").split()) < 6:
                    errs.append(f"{tag}: '{e['word']}' 예문이 6단어 미만")
        if st in ("reference", "implied-meaning"):
            p = it.get("passage", "")
            if "**" not in p and not UNDERLINE.search(p) and not re.search(r"[ⓐ-ⓩ]", p):
                errs.append(f"{tag}: 지문에 대상 표시(__밑줄__, **굵게** 또는 ⓐ)가 없음")
        if it.get("words_from_passages"):
            toks = corpus_tokens(exam, it["id"])
            words = [e["word"] for e in it.get("vocab_entries", [])] + list(it.get("match_left", []))
            for w in words:
                if not in_corpus(w, toks):
                    WARNINGS.append(f"{tag}: '{w}'가 이 문제지의 지문·보기에서 보이지 않음 (words_from_passages). "
                                    "불규칙 변화형으로 나왔다면 무시")
    if mc_count >= 5 and answers:
        top, n = answers.most_common(1)[0]
        if n / mc_count > 0.4:
            errs.append(f"정답 분포: {top + 1}번째 보기가 {n}/{mc_count} ({n / mc_count:.0%}). 40% 초과")
    errs += leak_errors(exam)
    absolute_warnings(exam)
    return errs


# every, all, 모든, 모두는 뺐다. 평범한 뜻으로 자주 쓰여 맞는 지적이 되지 못했다.
ABSOLUTE = re.compile(r"\b(always|never|only|none|nobody|must|completely|entirely)\b"
                      r"|반드시|항상|언제나|절대|전혀|결코|오직", re.I)


def absolute_warnings(exam: dict) -> None:
    """오답에만 절대 표현이 몰려 있으면 그 표현만 보고 지울 수 있다. 실패가 아니라 주의."""
    for it in exam["items"]:
        opts, a, st = it.get("options"), it.get("answer"), it["subtype"]
        if not opts or not isinstance(a, int) or not 0 <= a < len(opts):
            continue
        if st in POSITION or st in COMBO or st == "detail":
            continue
        wrong = [o for i, o in enumerate(opts) if i != a]
        hit = [o for o in wrong if ABSOLUTE.search(o)]
        if len(hit) >= 2 and not ABSOLUTE.search(opts[a]):
            WARNINGS.append(f"item {it['id']}: 오답 {len(hit)}개에만 절대 표현(always, never, 반드시 등)이 있음. 표현만 보고 지워질 수 있음")


def leak_errors(exam: dict) -> list[str]:
    """뜻 쓰기 문항의 정답(우리말 뜻)이나 표제어 풀이가 같은 문제지의 다른 곳에 드러나 있는가."""
    errs: list[str] = []
    ko_text: list[tuple[int, str]] = []
    notes: list[tuple[int, str]] = []
    for it in exam["items"]:
        if it.get("option_language") == "ko":
            ko_text += [(it["id"], o) for o in it.get("options") or []]
        if it.get("footnote"):
            notes.append((it["id"], it["footnote"]))
    for it in exam["items"]:
        if it["subtype"] != "meaning-write":
            continue
        for e in it.get("vocab_entries", []):
            word = e["word"].lower()
            for nid, note in notes:
                if re.search(rf"\b{re.escape(word)}\b", note.lower()):
                    errs.append(f"item {it['id']}: '{e['word']}'의 뜻이 문항 {nid}의 각주에 풀이돼 있음")
                    break
            for m in re.split(r"[,/;]", e.get("meaning") or ""):
                m = m.strip()
                key = m[:-1] if m.endswith("다") else m     # 빌리다 → 빌리
                if len(key) < 2:
                    continue
                where = sorted({nid for nid, t in ko_text if key in t})
                if where:
                    errs.append(f"item {it['id']}: '{e['word']}'의 정답 뜻({m})이 문항 {where}의 한국어 보기에 나옴")
                    break
    return errs


def check(exam: dict) -> list[str]:
    errs = schema_errors(exam)
    if errs:
        return errs  # 구조가 틀리면 뒤 검사가 의미 없음
    errs = structure_errors(exam)
    if exam["role"] == "generated":
        errs += writing_errors(exam)
    return errs


def partition(exam: dict) -> list[list[int]]:
    g: dict[str, list[int]] = {}
    for it in exam["items"]:
        if it.get("passage_group"):
            g.setdefault(it["passage_group"], []).append(it["id"])
    return sorted(g.values())


def compare_errors(src: dict, gen: dict) -> list[str]:
    errs: list[str] = []
    if src["role"] != "source":
        errs.append(f"첫 파일의 role이 source가 아님: {src['role']}")
    if gen["role"] != "generated":
        errs.append(f"둘째 파일의 role이 generated가 아님: {gen['role']}")
    for key, name in (("language", "발문 언어"), ("option_marker", "보기 표기")):
        if src.get(key) != gen.get(key):
            errs.append(f"{name}: 원본 {src.get(key)}, 생성 {gen.get(key)}")
    s_secs = [(s["title"], s["first"], s["last"]) for s in src.get("sections", [])]
    g_secs = [(s["title"], s["first"], s["last"]) for s in gen.get("sections", [])]
    if s_secs != g_secs:
        errs.append(f"영역(sections): 원본 {s_secs}, 생성 {g_secs}")
    if partition(src) != partition(gen):
        errs.append(f"지문 묶음 구조: 원본 {partition(src)}, 생성 {partition(gen)}")
    if len(src["items"]) != len(gen["items"]):
        errs.append(f"문항 수: 원본 {len(src['items'])}, 생성 {len(gen['items'])}")
        return errs
    seen_groups: set[str] = set()
    for a, b in zip(src["items"], gen["items"]):
        tag = f"item {a['id']}"
        if (a["type"], a["subtype"]) != (b["type"], b["subtype"]):
            errs.append(f"{tag}: 유형 {a['type']}/{a['subtype']} → {b['type']}/{b['subtype']}")
            continue

        def same(field: str, name: str, f=lambda v: v) -> None:
            va, vb = f(a.get(field)), f(b.get(field))
            if va != vb:
                errs.append(f"{tag}: {name} {va} → {vb}")

        size = lambda v: len(v) if v else 0  # noqa: E731
        same("options", "보기 수", size)
        same("option_language", "보기 언어")
        same("polarity", "일치/불일치 방향")
        same("points", "배점")
        same("points_per_part", "부분 배점")
        same("match_left", "짝짓기 왼쪽 항목 수", size)
        same("match_right", "짝짓기 오른쪽 항목 수", size)
        same("match_left_labels", "짝짓기 왼쪽 기호")
        same("match_right_labels", "짝짓기 오른쪽 기호")
        same("word_bank", "보기 상자 낱말 수", size)
        same("vocab_entries", "단어 항목 수", size)
        same("vocab_columns", "단어집 열")
        same("words_from_passages", "지문 출처 제약", bool)
        same("numbered_rows", "줄마다 번호", bool)
        same("other_label", "지원 범위 밖 유형 이름")
        pt_a, pt_b = len(en_words(a.get("prompt_text", ""))), len(en_words(b.get("prompt_text", "")))
        if pt_a and abs(pt_b - pt_a) > max(5, pt_a * 0.2):
            WARNINGS.append(f"{tag}: 딸린 글(prompt_text) 단어 수 {pt_a} → {pt_b} (±20%, 최소 ±5 초과)")
        same("given", "주어진 글 유무", bool)
        same("prompt_text", "요약문 유무", bool)
        nb_a, nb_b = len(BLANK.findall(a.get("passage", ""))), len(BLANK.findall(b.get("passage", "")))
        if nb_a != nb_b:
            errs.append(f"{tag}: 지문 빈칸 수 {nb_a} → {nb_b}")
        if abs(LEVELS.index(a["level"]) - LEVELS.index(b["level"])) > 2:
            errs.append(f"{tag}: 수준 {a['level']} → {b['level']} (두 칸 초과)")
        pw_a, pw_b = passage_words(a), passage_words(b)
        if pw_a and abs(pw_b - pw_a) > max(5, pw_a * 0.2):
            errs.append(f"{tag}: 지문 단어 수 {pw_a} → {pw_b} (±20%, 최소 ±5 초과)")
        sl_a, sl_b = sentence_lengths(a), sentence_lengths(b)
        if len(sl_a) >= 3 and sl_b and not (b.get("passage_group") and b["passage_group"] in seen_groups):
            avg_a, avg_b = sum(sl_a) / len(sl_a), sum(sl_b) / len(sl_b)
            if abs(avg_b - avg_a) > avg_a * 0.25:
                WARNINGS.append(f"{tag}: 문장 평균 길이 {avg_a:.1f} → {avg_b:.1f}단어 (±25% 초과). 수준이 달라졌을 수 있음")
        if b.get("passage_group"):
            seen_groups.add(b["passage_group"])
        if not set(a["topic_tags"]) & set(b["topic_tags"]):
            errs.append(f"{tag}: 소재 태그 겹침 없음 {a['topic_tags']} vs {b['topic_tags']} (사용자가 다른 소재를 요청했으면 무시)")
    return errs


def all_sentence_lengths(exam: dict) -> list[int]:
    out: list[int] = []
    seen: set[str] = set()
    for it in exam.get("items", []):
        g = it.get("passage_group")
        if g and g in seen:
            continue
        if g:
            seen.add(g)
        out += sentence_lengths(it)
    return out


def stats(exam: dict) -> None:
    """구조 검사 없이 센다. 수준(level)을 아직 적지 않은 파일도 받는다."""
    print(f"{exam.get('title', '(제목 없음)')}  [{exam.get('role', '?')}, 발문 {exam.get('language', '?')}, "
          f"보기 표기 {exam.get('option_marker', '?')}, 수준 {exam.get('source_level', '미정')}]")
    seen: set[str] = set()
    all_sent: list[int] = []
    print(f"{'id':>3}  {'type/subtype':<26} {'지문':>5} {'문단':>4} {'문장평균':>7}  보기 낱말 수")
    for it in exam.get("items", []):
        g = it.get("passage_group")
        sents = sentence_lengths(it)
        if not (g and g in seen):
            all_sent += sents
        if g:
            seen.add(g)
        avg = f"{sum(sents) / len(sents):.1f}" if sents else "-"
        opts = it.get("options")
        o = str([opt_len(x) for x in opts]) if opts else ""
        extra = ""
        if "word_bank" in it:
            extra = f"보기 상자 {len(it['word_bank'])}, 빈칸 {len(BLANK.findall(it.get('passage', '')))}"
        if "match_left" in it:
            extra = f"짝 {len(it['match_left'])} : {len(it.get('match_right', []))}"
        if "vocab_entries" in it:
            extra = f"단어 {len(it['vocab_entries'])}개"
        if it.get("prompt_text"):
            extra += f"  딸린 글 {len(en_words(it['prompt_text']))}단어"
        if it.get("numbered_rows"):
            extra += "  줄마다 번호"
        if it.get("type") == "other":
            extra += f"  지원 범위 밖({it.get('other_label', '?')})"
        kind = f"{it.get('type', '?')}/{it.get('subtype', '?')}"
        print(f"{it.get('id', '?'):>3}  {kind:<26} {passage_words(it) or '-':>5} {paragraph_count(it) or '-':>4} {avg:>7}  "
              f"{o}{extra}{'  [' + g + ']' if g else ''}")
    if all_sent:
        print(f"\n전체 문장 평균 길이 {sum(all_sent) / len(all_sent):.1f}단어 ({len(all_sent)}문장). "
              "수준 판단은 references/subject-english.md 1절 참고")
    print("지문 단어 수는 영어 낱말만 셉니다(주어진 글 포함, 빈칸·기호·각주 제외). 생성물의 목표는 이 값의 ±20%입니다.")


def report(errs: list[str]) -> int:
    if errs:
        print(f"실패 {len(errs)}건")
        for e in errs:
            print(" -", e)
    else:
        print("통과")
    if WARNINGS:
        print(f"주의 {len(WARNINGS)}건 (실패로 세지 않음)")
        for w in WARNINGS:
            print(" -", w)
    return 1 if errs else 0


def main() -> int:
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if args else 1
    if args[0] == "--stats":
        if len(args) < 2:
            print(__doc__)
            return 1
        if not args[1].lower().endswith(".json"):
            try:
                text = Path(args[1]).read_text(encoding="utf-8")
            except (FileNotFoundError, UnicodeDecodeError) as e:
                print(f"읽을 수 없음: {args[1]}: {e}", file=sys.stderr)
                return 1
            sents = sentence_lengths({"passage": text})
            print(f"{args[1]}: 영어 낱말 {len(en_words(text))}개, 문장 {len(sents)}개, "
                  f"문장 평균 길이 {sum(sents) / len(sents):.1f}단어" if sents else f"{args[1]}: 영어 문장을 찾지 못함")
            print("수준 판단은 references/subject-english.md 1절 참고. 문제지를 통째로 넣으면 보기·발문도 함께 세어집니다.")
            return 0
        stats(load(args[1]))
        return 0
    if args[0] == "--compare":
        if len(args) < 3:
            print(__doc__)
            return 1
        src, gen = load(args[1]), load(args[2])
        errs = [f"[원본] {e}" for e in check(src)] + [f"[생성] {e}" for e in check(gen)]
        if not any(e.startswith(("[원본] schema", "[생성] schema")) for e in errs):
            errs += [f"[비교] {e}" for e in compare_errors(src, gen)]
            a, b = all_sentence_lengths(src), all_sentence_lengths(gen)
            if a and b:
                ma, mb = sum(a) / len(a), sum(b) / len(b)
                print(f"참고: 문제지 전체 문장 평균 길이 {ma:.1f} → {mb:.1f}단어 ({(mb - ma) / ma:+.0%}). "
                      "한 문장짜리 문항은 문항별 주의에 걸리지 않으므로 이 값으로 봅니다.")
        return report(errs)
    if args[0] == "--words-in":
        if len(args) < 3:
            print(__doc__)
            return 1
        try:
            toks = {w.lower() for w in en_words(Path(args[1]).read_text(encoding="utf-8"))}
        except FileNotFoundError:
            print(f"파일을 찾을 수 없음: {args[1]}", file=sys.stderr)
            return 1
        exam = load(args[2])
        words = [e["word"] for it in exam.get("items", []) for e in it.get("vocab_entries", [])]
        missing = [w for w in words if not in_corpus(w, toks)]
        print(f"표제어 {len(words)}개 중 입력 글에서 찾은 것 {len(words) - len(missing)}개")
        # 불규칙 변화형(sought ← seek)은 가려낼 수 없어서 실패가 아니라 주의로 낸다
        WARNINGS.extend(f"'{w}'가 입력 글에서 보이지 않음. 입력 글에서 직접 찾아보고, 없으면 그 단어를 뺌" for w in missing)
        return report([])
    return report(check(load(args[0])))


if __name__ == "__main__":
    sys.exit(main())
