# ANYQUIZ 로드맵

상태 표기: `[x]` 완료, `[ ]` 예정, `[~]` 진행 중. 단계를 넘어갈 때 이 파일을 갱신한다.

## 왜 스킬인가 (플러그인이 아니라)

- 사용자(교사·학원·수험생)는 claude.ai 앱을 쓴다. claude.ai는 스킬(zip)은 받지만 플러그인은 받지 않는다.
- 훅·MCP·별도 서브에이전트가 필요한 기능이 없다. `scripts/`, `references/`, `assets/`로 충분하다.
- 같은 폴더가 Claude Code, claude.ai, Codex CLI에서 동작한다.
- 스킬은 사용자 계정 안에서 돌아가므로 기존 로컬 웹페이지와 달리 API 키 배포가 필요 없다.

## 0단계. 범위 고정 `[x]`

- 과목: 영어. 유형: cloze / vocab / reading. 모드: format / passage / vocab
- 입력: 텍스트 PDF, 텍스트. 스캔 PDF 제외
- 출력: 마크다운 + DOCX(요청 시)
- 확정된 설계 결정은 `CLAUDE.md` 참고

## 1단계. 스킬 v0.1 `[x]` (여기까지 claude.ai 세션에서 작성)

- `skills/anyquiz-english/SKILL.md` 3단계 절차
- `references/schema.md`, `question-types.md`, `subject-english.md`
- `scripts/extract.py`, `validate_schema.py`, `overlap.py`, `export_docx.py`, `exam.schema.json`
- `assets/exam-template.docx`
- `eval/samples/`로 스크립트 회귀 확인 완료

## 2단계. 실제 호출과 실패 목록 `[~]` (Claude Code에서)

- [x] `.claude/skills/`에 심볼릭 링크 후 `/anyquiz-english` 호출 확인 (Windows는 `mklink /J` 정션. `eval/results/round-00.md`)
- [x] 문제지 5장으로 format 모드 실행. 매번 다음을 기록 → `eval/results/round-00.md` (01, 02 완료. 2026-11-09), `round-01.md` (수정된 스킬로 01·02 재실행 + 03. 2026-11-13, 04·05 추가. 2026-11-19)
  - 분석 표가 맞았는가 (유형·수준·문항 수)
  - 생성물이 스키마를 통과했는가
  - 정답이 맞았는가 (직접 풀어서)
  - 어디서 틀렸는가 (유형별로)
- [ ] passage 모드 3회, vocab 모드 3회 동일하게
- [ ] 실패 유형을 빈도순으로 정리. 이것이 4단계의 입력
- [ ] 발견한 "나쁜 예"를 `question-types.md`에 추가

알려진 미완성:
- `multi-blank`, `word-bank`, `synonym-match`, `definition-match`의 예시가 없다. 실제 원본에서 그 유형이 나올 때 채운다.
- `extract.py` 2단 편집 처리는 2026-11-19에 넣었다(`eval/results/extract-2col.md`). 남은 한계: 단 안의 표에서 여러 줄 셀이 줄 단위로 섞임, 굵게·밑줄 표시 소실, 3단 이상 미지원.

## 3단계. 평가 세트 `[ ]`

- [~] `eval/sources/`에 **직접 제작한** 문제지 10~15장, **텍스트(.md)로**. 파일명 `NN-<level>-<types>.md`. 정답·해설 포함 (01~05 완료)
  - 유형·수준·스타일을 섞는다: 수능형(5지선다, 한국어 발문), 내신형(서술형 포함), 토익형(4지선다, 영어 발문) 중 둘 이상
  - 내용 평가는 텍스트로 한다. 레이아웃은 내용 평가와 무관하다
  - 파싱 확인용으로만 **PDF 2장**을 따로 둔다(`eval/sources/pdf/`): 하나는 1단, 하나는 2단 편집(2단은 `05-A2-2col.pdf`로 완료, 1단은 아직 없음). 내용은 아무거나. extract.py가 열 순서를 섞지 않는지만 본다
  - 문제지마다 **구조 조합을 다르게**: 유형 비율, 문항 수, 보기 수(4/5), 발문 언어, 배점. format 모드가 베끼는 것이 구조이므로 구조가 다양해야 한다
  - Claude에게 만들게 하지 않는다. 생성기로 평가 세트를 만들면 생성기 편향이 기준에 들어간다
  - 이 세트는 저장소에 커밋된다. 누구나 재현할 수 있는 회귀 테스트가 목적이다
- [ ] 각 문제지에 대해 분석 정답 JSON 작성 → `eval/sources/NN.expected.json` (분석 단계 채점용). Claude가 초안을 만들고 사용자가 확인한 뒤 넣는다
- [ ] 루브릭 작성 → `eval/rubrics/content-similarity.md` (1~5점, 같은 단원·난이도·모호성)
- [ ] 배치 실행 스크립트 → `eval/run.sh`: 원본마다 `claude -p`로 5회 생성, `validate_schema.py --compare`와 `overlap.py` 자동 실행, 결과를 `eval/results/round-NN/`에 저장
- [ ] LLM 채점 스크립트 → `eval/judge.sh`: 루브릭으로 내용 충실도 채점 (생성물만 보고, 원본·생성 과정은 보지 않게)
- [ ] 기준선 측정 → `eval/results/baseline.md`

`claude -p` 배치 예시(D편 참고):
```
claude -p "eval/sources/03.pdf를 format 모드로, 같은 문항 수로 생성해 JSON만 출력" \
  --allowedTools "Read,Bash(python3 *)" --max-turns 20 --max-budget-usd 1.00 \
  --output-format json > eval/results/round-01/03-run1.json
```

## 4단계. 반복 개선 `[ ]`

라운드마다: 실패 사례 분류 → 가장 많은 유형 하나 고치기 → 전체 재측정 → `eval/results/round-NN.md`에 기록.

고치는 수단 (효과 순):
1. `question-types.md`에 나쁜 예 + 고친 예 추가
2. 스키마 필드 추가 (예: 보기 길이 균형이 깨지면 `option_length_balance`)
3. 검증 단계 강화 (오답 보기마다 이유 쓰기 등)
4. SKILL.md 절차 수정 (마지막 수단. 절차가 자주 바뀌면 설계가 틀린 것)

### 라운드 완료 조건 (이 셋이 다 있어야 라운드가 끝난 것)

1. `eval/results/round-NN.md`에 실패 유형별 건수 표
2. 이번 라운드에 고친 것 **하나**와, 근거가 된 실패 사례 번호
3. 전체 재측정 숫자를 이전 라운드와 나란히

### 중단 조건 (튜닝을 멈추고 설계를 의심할 시점)

- 두 라운드 연속 정답 정확성이 오르지 않음 → 프롬프트 수정 중단. 스키마 누락 필드나 분석 단계 오류를 먼저 의심
- 한 subtype만 반복 실패 → v1.0에서 제외하고 README "지원 안 함"에 명시. 전부 되게 하려다 전체가 늦어지지 않게

### 종료 조건 (pass^5 기준)
- 형식 충실도 100%
- 정답 정확성 95% 이상
- 내용 충실도 평균 4.0 이상
- 중복률 15% 미만 문항 100%

## 5단계. 공개 `[ ]`

- [ ] `skills-ref validate skills/anyquiz-english` (agentskills.io 참조 구현)
- [ ] README에 지원 범위·알려진 한계·이용 안내
- [ ] 세 곳 설치 테스트: claude.ai(zip 업로드), Claude Code(`.claude/skills/`), Codex CLI(`.agents/skills/`)
- [ ] **낯선 사람 테스트**: 이 프로젝트를 모르는 사람 1명이 README만 보고 설치해 문제지 한 장을 뽑는다. 실패하면 숫자가 좋아도 공개하지 않는다
- [ ] GitHub 릴리스 태그 `v1.0.0`

## 6단계. 플러그인 승격 `[ ]` (조건부)

다음 중 하나가 필요해지면 `.claude-plugin/plugin.json`으로 감싼다. 스킬 폴더는 그대로 `skills/` 아래 유지.

- 검증을 별도 서브에이전트(`agents/verifier.md`, model: haiku)로 분리해 비용 절감
- `/anyquiz --count 20 --mode format` 같은 옵션 있는 명령
- 정답 키 없는 출력을 훅으로 차단
- Claude Code 마켓플레이스 배포 (`.claude-plugin/marketplace.json`)

## 일정 감각

| 단계 | 기간 |
| :- | :- |
| 2 | 1~2일 |
| 3 | 3~4일 |
| 4 | 2~3주 |
| 5 | 2~3일 |

4단계 길이는 3단계 평가 세트의 품질에 달려 있다. 평가 세트를 대충 만들면 4단계가 끝나지 않는다.
