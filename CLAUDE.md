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
4. passage 모드는 사용자가 올린 지문을 결과에 그대로 싣는다.
5. 단어집은 입력 텍스트에서 추출 / 입력 없이 생성 둘 다 지원.
6. 생성은 반드시 분석 → 생성 → 검증 3단계. 한 번에 하지 않는다.
7. 스캔 PDF, 듣기, 영어 외 과목은 지원하지 않는다고 말하고 멈춘다.

## 정확도 정의 (PLAN.md 3단계 기준)

| 축 | 측정 | 목표 |
| :- | :- | :- |
| 형식 충실도 | `validate_schema.py --compare` | 100% |
| 정답 정확성 | 독립 풀이 일치 + 사람 표본 | 95% 이상 |
| 내용 충실도 | LLM 루브릭 1~5점 | 평균 4.0 이상 |
| 신규성 | `overlap.py` 6-gram | 15% 미만 |

측정은 pass^k (같은 입력 5회 전부 통과)로 한다. 한 번 성공률로 보고하지 않는다.

## 작업 규칙

- 스킬 파일을 고친 뒤에는 반드시 `/anyquiz-english`로 실제 호출해 본다. 파일만 보고 판단하지 않는다.
- `references/question-types.md`의 "나쁜 예"는 실제 실패 사례에서만 추가한다. 상상해서 쓰지 않는다.
- 평가 세트(`eval/sources/`)의 문제지는 사용자가 직접 만들어 제공한다. Claude가 만들지 않는다(생성기 편향이 기준에 들어간다).
- `scripts/`는 `python3 -I`로 실행해도 동작해야 한다(외부 의존: pdfplumber, pypdf, jsonschema, python-docx). `-I`에서는 스크립트끼리 import가 안 되므로 공용 모듈을 만들지 않는다.
- 스크립트 수정 후 `eval/samples/`로 회귀 확인:
  ```
  python3 skills/anyquiz-english/scripts/validate_schema.py eval/samples/sample-generated.json
  python3 skills/anyquiz-english/scripts/validate_schema.py eval/samples/sample-en-group.json
  python3 skills/anyquiz-english/scripts/render_md.py eval/samples/sample-en-group.json
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
