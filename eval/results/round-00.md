# round-00: 첫 실제 호출 (PLAN.md 2단계)

날짜: 2026-11-09. 환경: Claude Code 2.1.205 (Windows 11, VS Code 확장). 생성·분석은 이 세션의 모델(Fable 5.1), 독립 풀이는 정답지 없이 별도 서브에이전트.

## 준비

| 항목 | 결과 |
| :- | :- |
| `.claude/skills/anyquiz-english` 링크 | Git Bash `ln -s`는 Windows에서 **복사본**을 만듦. `mklink /J` 정션으로 교체. `skills/`에 파일을 만들면 링크 쪽에도 보임 확인 |
| `agentskills validate` | Valid skill |
| `/anyquiz-english` 호출 | 새 `claude -p` 세션에서 인식됨. 이 세션에서도 재시작 후 Skill 도구 목록에 떠서 직접 호출함 |
| 메모 | 같은 세션 안에서 새로 링크한 스킬은 Skill 도구 목록에 안 뜸(세션 시작 때 고정) |

## 절차 메모 (이 라운드에서 정한 것)

- 중간 산출물은 `eval/results/round-00/`에 둔다(`.gitignore` 대상): `NN-source.json`(분석), `NN-run1.json`(생성), `NN-run1.md`(출력)
- 어휘 영역(단어 10개 × 2점)은 **문항 1개**(`vocab/meaning-write`, points 20, vocab_entries 10)로 모델링. 원본 표지의 "22문항"과 다르게 세므로 compare는 13 vs 13으로 맞춤
- 지문을 공유하는 문항은 각 문항에 지문을 **중복 저장**. 스키마가 문항 단위라 다른 방법이 없음
- 검증 순서: 독립 풀이(서브에이전트, 문제지만 제공) → `validate_schema.py --compare` → `overlap.py` → 풀이자 지적 반영 → 재검증
- JSON → 마크다운 렌더러가 스킬에 없어 스크래치패드에 임시로 씀(`render.py`). 2단계 끝나면 `scripts/`에 넣을지 결정

## format 모드 실행 기록

### 01. `01-B1-reading-cloze-vocab.md` (중3 내신, ko, 5지선다)

| 항목 | 결과 |
| :- | :- |
| 분석 표 정확 (유형·수준·문항 수) | **맞음**. 독해 8(main-idea, detail, reference, implied-meaning / title, detail, inference×2), 빈칸 4(single-blank, 11번은 연결어), 어휘 1묶음. B1. 발문 ko |
| 스키마 통과 (`validate_schema.py --compare`) | **통과** (1회 수정 없이). 지문 길이 146→168, 156→175, 빈칸 47~58→50~62 |
| 중복률 (`overlap.py`, 15% 미만) | **전 문항 0%** |
| 정답 정확 (독립 풀이) | **12/12** 객관식, 어휘 10/10 |
| 틀린 곳 (유형별) | 정답 오류 없음. 표현 지적 2건: ① cloze 10번 정답 보기 "remember the speech without effort"가 지문("without her notes")보다 과장 → "memorize the speech more easily"로 수정. ② vocab 13번 발문 "위 지문에 나온"이 바로 위 지문 하나로 읽힘 → "1~12번 지문에 나온"으로 수정. 그 외: vocab `record`가 동사/명사 둘 다 가능(해설에 유사 뜻 인정 명시로 처리), cloze 12번 오답 ④가 다른 오답보다 모호함(변별엔 무영향) |

### 02. `02-B1plus-reading-cloze-vocablist-en.md` (고1, en, 4지선다, 단어집 채점 안 함)

| 항목 | 결과 |
| :- | :- |
| 분석 표 정확 (유형·수준·문항 수) | 독해 6(title, detail, inference / main-idea, reference, inference), 빈칸 2(74·86단어, 14점), 단어집 1(word-list 15개, 0점). 수준 B1+(문장 평균 16단어, tentative·interpretation 등 학술어) → 스키마엔 B1으로 기록 |
| 스키마 통과 (`validate_schema.py --compare`) | **통과**. 지문 176→198, 186→202, 빈칸 74→70, 86→95 |
| 중복률 (`overlap.py`, 15% 미만) | **전 문항 0%** |
| 정답 정확 (독립 풀이) | **8/8** 객관식, 단어집 15/15 뜻 일치 |
| 틀린 곳 (유형별) | 정답 오류 없음. 지적 3건: ① reference 5번 정답 보기가 유일하게 10단어로 길어 길이 단서 → 7단어로 축약(`validate_schema.py`의 길이 규칙은 통과했었음. 규칙이 "2배 초과 + 3단어 차" 둘 다일 때만 잡아서 이런 경우를 못 봄). ② 단어집 발문 "Inflected forms are listed in their base forms"가 어색 → 원본 문구 그대로였으나 "Words are listed in their base forms"로 수정. ③ inference 3번 정답이 마지막 문장의 거의 직역 수준 패러프레이즈라 "추론" 난도가 낮음(정답은 명확, 수정 안 함). 수준: 지문 2(종·기록 보관소)가 B2 초입, 빈칸 2개는 B1으로 약간 쉬움 |

**설계 질문 (02에서 발견):** 원본은 영어 발문인데 보기 번호가 ①②③④다. 설계 결정 2번(en → (A)(B)(C)(D))을 따르면 생성물의 보기 표기가 원본과 달라진다. format 모드가 "형식 모사"라면 원본 표기를 따라야 하는지 사용자 결정 필요.

## 실패 유형 빈도 (5장 완료 후 정리)

| 실패 유형 | 건수 | 사례 번호 |
| :- | :- | :- |
| 정답 보기가 지문보다 과장된 표현 | 1 | 01-10 |
| 정답 보기만 눈에 띄게 긺 (스크립트 미검출) | 1 | 02-05 |
| 발문 문구 불명확·어색 | 2 | 01-13, 02-09 |
| inference 문항이 사실상 detail 수준 | 1 | 02-03 |

2장 기준 정답 오류 0건. 지적은 전부 표현·난도 쪽. 5장 채운 뒤 가장 많은 유형 하나를 4단계 입력으로 삼는다.
