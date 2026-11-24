# ANYQUIZ

영어 문제 생성 Agent Skill 저장소. 이 파일은 Claude Code가 세션 시작 때 읽는다. 짧게 유지한다(200줄 이하). 상세 계획은 `PLAN.md`, 스킬 작성 규칙은 `skills/anyquiz-english/references/`에 있다.

## 무엇을 만드는가

- 스킬 하나: `skills/anyquiz-english/` (Agent Skills 표준, agentskills.io)
- 입력: 텍스트 PDF 또는 텍스트. 출력: 마크다운 문제지 + 정답·해설, 요청 시 DOCX
- 유형: cloze(빈칸), vocab(단어집), reading(독해). 모드: format(형식 모사), passage(본문 기반), vocab
- 플러그인이 아니라 스킬이다. 플러그인 승격 조건은 PLAN.md 6단계. 조건이 생기기 전에는 `.claude-plugin/`을 만들지 않는다.

## 확정된 설계 결정 (바꾸려면 사용자에게 먼저 묻는다)

1. 과목은 영어 하나. 다른 과목은 `references/subject-<name>.md` 추가로 확장하되 지금은 하지 않는다.
2. 발문·해설 언어와 보기 번호 표기는 **각각 원본을 따른다**(서로 묶지 않는다. 영어 발문 + ①②③④ 가능). 원본이 없는 passage/vocab 모드는 언어를 사용자에게 묻고, 보기 표기는 사용자 지정이 없으면 ①②③④⑤
3. format 모드의 새 지문은 원본과 같은 소재, 다른 내용.
4. passage 모드는 사용자가 올린 지문을 결과에 그대로 싣는다. 글자는 바꾸지 않고 문항에 필요한 표시(밑줄, ⓐ)만 더할 수 있다.
5. 단어집은 입력 텍스트에서 추출 / 입력 없이 생성 둘 다 지원.
6. 생성은 반드시 분석 → 생성 → 검증 3단계. 한 번에 하지 않는다.
7. 스캔 PDF, 듣기, 영어 외 과목은 지원하지 않는다고 말하고 멈춘다.
8. JSON은 스키마 v2 하나를 두 역할로 쓴다. `source`(원본 분석)는 형식 정보만 담고 원본에 없는 것을 지어 넣지 않는다. `generated`(생성물)에만 정답·해설·오답 이유를 요구하고 작성 규칙 검사를 적용한다.
9. 정답지가 없는 원본도 받는다(`answer_key: none`). 새 문제를 만드는 데 원본 정답은 필요 없다.
10. 빈칸 문제는 보기로 나눈다. 보기가 단어면 `cloze/single-blank`, 구·절이면 `reading/blank-inference`.
11. 발문 언어, 해설 언어, 보기 언어, 보기 표기는 서로 묶지 않고 각각 원본을 따른다.
12. 지문 단어 수·보기 길이는 JSON에 적지 않고 스크립트가 센다(`validate_schema.py --stats`).
13. 검증에서 다시 만드는 조건은 둘이다: 정답 불일치, 답이 둘 이상 가능. "보기만으로 풀림"은 재지 않는다(원본도 지문 없이 30/30 풀렸다. round-02). 겉으로 드러나는 단서(정답 길이, 오답의 절대 표현, 어휘 뜻 누출)만 스크립트가 본다.
14. 고치는 횟수는 문제지 단위로 두 번까지. 그래도 남은 문항은 빼지 않고 `review`에 적어 출력 맨 위에 "검토 필요 문항"으로 표시한다.
15. 새 지문의 인물 이름은 모델이 고르지 않고 `pick_names.py`가 뽑는다(원본에 나온 이름은 뺀다). 장소·사물·전개 방식 뽑기는 뺐다(round-03: 줄거리는 그대로였고 어색한 세부가 생겼다).
16. 발문이 없는 원본 문항은 발문 없이 담는다. 영역 지시문(`sections[].instruction`)이나 묶음 안내문이 대신한다.
17. "밑줄 친" 대상은 `__…__`로 담고 실제 밑줄로 출력한다. 발문을 출력에 맞춰 바꾸지 않는다.
18. passage 모드의 문항 유형은 시작할 때 묻고, 말이 없으면 요지·내용 일치·추론·제목·요약문 순으로 쓴다.
19. 원본이 없는 단어집의 기본 열은 단어·품사·뜻이다. 예문은 요청했을 때만 넣는다.
20. 각주는 형식 비교 대상이 아니다. 새 지문에 수준을 넘는 낱말이 있을 때만 단다.

## 정확도 정의 (PLAN.md 3단계 기준)

| 축 | 측정 | 목표 |
| :- | :- | :- |
| 형식 충실도 | `validate_schema.py --compare` | 100% |
| 정답 정확성 | 독립 풀이 일치 + 사람 표본 | 95% 이상 |
| 내용 충실도 | LLM 루브릭 1~5점 | 평균 4.0 이상 |
| 신규성 | `overlap.py` 6-gram | 15% 미만 |
| 실행 간 다양성 | `overlap.py run-a.json run-b.json` (같은 원본의 다른 실행끼리) | 15% 미만 |

측정은 pass^k (같은 입력 5회 전부 통과)로 한다. 한 번 성공률로 보고하지 않는다.

## 작업 규칙

- 스킬 파일을 고친 뒤에는 반드시 `/anyquiz-english`로 실제 호출해 본다. 파일만 보고 판단하지 않는다.
- `references/question-types.md`의 "나쁜 예"는 실제 실패 사례에서만 추가한다. 상상해서 쓰지 않는다. 스킬 파일에는 평가 세트의 문제지·문항 번호를 적지 않는다(어느 사례가 어느 문항인지는 `eval/results/`에만 적는다).
- 평가 세트(`eval/sources/`)의 문제지는 사용자가 직접 만들어 제공한다. Claude가 만들지 않는다(생성기 편향이 기준에 들어간다).
- `scripts/`는 `python3 -I`로 실행해도 동작해야 한다(외부 의존: pdfplumber, pypdf, jsonschema, python-docx). `-I`에서는 같은 폴더 import가 안 된다. 스크립트끼리 코드를 나눠 쓸 때는 `export_docx.py`처럼 `importlib`로 경로를 지정해 불러온다. 출력 구조는 `render_md.py`의 `build_blocks()` 한 곳에서 만든다.
- 새 유형이나 필드를 더할 때는 네 곳을 함께 고친다: `schema.md`의 "유형별 담는 법", `exam.schema.json`, `validate_schema.py`, `render_md.py`. 한 곳만 고치면 04번의 짝짓기처럼 문서대로 담았는데 출력이 망가진다.
- 스크립트 수정 후 `eval/samples/`로 회귀 확인:
  ```
  python3 skills/anyquiz-english/scripts/validate_schema.py --compare eval/samples/sample-source.json eval/samples/sample-generated.json
  python3 skills/anyquiz-english/scripts/validate_schema.py --compare eval/samples/sample-en-group.source.json eval/samples/sample-en-group.json
  python3 skills/anyquiz-english/scripts/validate_schema.py --compare eval/samples/sample-nostem.source.json eval/samples/sample-nostem.json
  python3 skills/anyquiz-english/scripts/render_md.py eval/samples/sample-generated.json
  python3 skills/anyquiz-english/scripts/overlap.py eval/samples/sample-source.txt eval/samples/sample-generated.json
  ```
- 커밋 메시지는 한국어, 한 줄 요약 + 필요 시 본문.

## 이 저장소의 훅 (`.claude/settings.json`)

| 훅 | 하는 일 |
| :- | :- |
| PreToolUse Edit\|Write | `eval/sources/` 수정 차단. 기준 데이터는 사람만 고친다 |
| PostToolUse Edit\|Write | 스킬 파일이 바뀌면 `agentskills validate` + 스크립트 컴파일 + 샘플 회귀. 실패하면 되돌아옴 |
| Stop | 스킬이 바뀌었는데 `eval/results/`에 기록이 없으면 알림 |

훅이 거부하면 우회하지 말고 원인을 고친다. 훅 자체를 고쳐야 하면 사용자에게 먼저 말한다.

훅 스크립트는 bash + Python만 쓴다(jq 없음). Windows에서는 Git Bash와 `python`이 PATH에 있어야 한다. 데스크톱 앱·VS Code 확장·터미널 어디서든 로컬 세션이면 같은 설정으로 동작한다.

## 로컬에서 스킬 쓰기

```
mkdir -p .claude/skills
ln -s ../../skills/anyquiz-english .claude/skills/anyquiz-english
```

Windows Git Bash의 `ln -s`는 복사본을 만든다. 대신 `cmd /c "mklink /J .claude\skills\anyquiz-english skills\anyquiz-english"`.

이후 세션에서 `/anyquiz-english` 또는 "이 문제지와 비슷한 문제 만들어 줘"로 호출.

## 하지 않는 것

- `bin/` 최상위 폴더 (조직 동기화에서 거부됨). 실행 파일은 `scripts/`.
- SKILL.md 500줄 초과. 넘으면 `references/`로 뺀다.
- 실존 인물·수치를 지어낸 지문. 익명화한다.
