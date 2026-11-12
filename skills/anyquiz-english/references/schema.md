# 문항 JSON 스키마

분석 단계의 출력이자 생성 단계의 입력입니다. 원본 문제지(`format` 모드)와 생성 결과 모두 같은 스키마를 씁니다. 두 JSON을 나란히 비교하면 "비슷함"이 수치로 보입니다.

기계 검증용 JSON Schema는 `scripts/exam.schema.json`에 있고, `scripts/validate_schema.py`가 그 파일로 검사합니다.

## 최상위

```json
{
  "title": "2학년 1학기 중간고사 영어",
  "mode": "format",
  "language": "ko",
  "option_marker": "circled",
  "source_level": "B1",
  "total_points": 100,
  "items": [ ... ]
}
```

| 필드 | 타입 | 필수 | 설명 |
| :- | :- | :- | :- |
| `title` | string | 예 | 문제지 제목 |
| `mode` | `format` \| `passage` \| `vocab` | 예 | 생성 모드 |
| `language` | `ko` \| `en` | 예 | 발문·해설 언어. 보기 번호 표기와는 무관 |
| `option_marker` | `circled` \| `letter` \| `number` | 예 | 보기 번호 표기. `circled` ①②③, `letter` (A)(B)(C), `number` (1)(2)(3). `format` 모드는 **원본 표기 그대로**. 원본이 없으면 사용자 지정, 없으면 `circled` |
| `source_level` | `A1`~`C2` | 예 | 전체 수준 (CEFR) |
| `total_points` | number | 아니오 | 총점. 없으면 문항 배점 합 |
| `items` | array | 예 | 문항 배열. 1개 이상 |

## 문항 (`items[]`)

```json
{
  "id": 3,
  "type": "reading",
  "subtype": "blank-inference",
  "level": "B1",
  "points": 3,
  "topic_tags": ["environment", "recycling"],
  "passage": "Plastic waste has become ...",
  "passage_words": 142,
  "stem": "다음 빈칸에 들어갈 말로 가장 적절한 것은?",
  "options": ["...", "...", "...", "...", "..."],
  "answer": 2,
  "explanation": "두 번째 문단에서 ...",
  "distractor_notes": ["①은 지문과 반대", "③은 언급 없음", "④는 부분 정보", "⑤는 범위 초과"]
}
```

| 필드 | 타입 | 필수 | 설명 |
| :- | :- | :- | :- |
| `id` | integer | 예 | 1부터 순번 |
| `type` | `cloze` \| `vocab` \| `reading` | 예 | 문제 유형 |
| `subtype` | string | 예 | 유형 세부. 아래 표 참고 |
| `level` | `A1`~`C2` | 예 | 문항 수준 |
| `points` | number | 예 | 배점 |
| `topic_tags` | string[] | 예 | 소재 태그 2~4개, 영어 소문자 |
| `passage` | string | reading·cloze는 예 | 지문. vocab은 생략 가능 |
| `passage_words` | integer | passage 있으면 예 | 지문 단어 수 |
| `passage_group` | string | 아니오 | 지문 하나에 문항이 여러 개 딸릴 때의 묶음 이름(예: `"g1"`). 같은 묶음의 문항은 `passage`가 완전히 같아야 하고 서로 이어진 번호여야 함. 출력할 때 지문은 묶음 첫 문항 앞에 한 번만 나옴 |
| `stem` | string | 예 | 발문 |
| `options` | string[] | 객관식은 예 | 보기. 4개 또는 5개 |
| `answer` | integer \| string | 예 | 객관식은 보기 인덱스(0부터), 주관식은 정답 문자열 |
| `explanation` | string | 예 | 해설 두 문장 이내 |
| `distractor_notes` | string[] | 객관식은 예 | 오답 보기마다 한 구절. 길이 = options 수 − 1 |
| `vocab_entries` | array | vocab은 예 | 아래 단어집 항목 |

## subtype 목록

| type | subtype | 설명 |
| :- | :- | :- |
| `cloze` | `single-blank` | 한 문장 또는 짧은 단락에 빈칸 하나, 보기 4~5개 |
| `cloze` | `multi-blank` | 빈칸 (A)(B)(C)에 들어갈 말의 조합 |
| `cloze` | `word-bank` | 보기 상자에서 골라 채우기 (주관식) |
| `vocab` | `word-list` | 단어·품사·뜻·예문 표 |
| `vocab` | `synonym-match` | 유의어 짝짓기 |
| `vocab` | `definition-match` | 영영 뜻풀이 짝짓기 |
| `vocab` | `meaning-write` | 단어의 문맥상 우리말 뜻 쓰기 (주관식). 내신 어휘 영역의 기본형 |
| `reading` | `main-idea` | 요지·주제 |
| `reading` | `title` | 제목 |
| `reading` | `blank-inference` | 빈칸 추론 (지문 안 빈칸) |
| `reading` | `detail` | 내용 일치·불일치 |
| `reading` | `order` | 글의 순서 |
| `reading` | `insertion` | 문장 삽입 |
| `reading` | `irrelevant` | 흐름과 무관한 문장 |
| `reading` | `summary` | 요약문 빈칸 |
| `reading` | `reference` | 밑줄 친 대명사·표현이 가리키는 것 (지칭 추론) |
| `reading` | `implied-meaning` | 밑줄 친 문장·표현에 담긴 의미 (함축 의미) |
| `reading` | `inference` | 글을 바탕으로 한 추론: 이유, 인물의 생각, 다음에 일어날 일 등 |

새 subtype이 필요하면 이 표에 먼저 추가하고 `question-types.md`에 규칙을 씁니다.

### 보기가 지문 안에 있는 유형의 규약

`order`(글의 순서)와 `insertion`(문장 삽입)은 보기와 지문이 다른 유형처럼 나뉘지 않습니다. 실행마다 다르게 담기지 않도록 이렇게 고정합니다.

| subtype | `passage`에 담는 것 | `options`에 담는 것 | `answer` |
| :- | :- | :- | :- |
| `order` | 주어진 글, 그다음 `(A)` `(B)` `(C)` 단락을 **문제지에 나온 순서대로** | 순서 조합 5개. 예: `"(B)-(C)-(A)"` | 조합의 인덱스 |
| `insertion` | **주어진 문장을 맨 앞에**, 그다음 `( ① )`~`( ⑤ )` 위치 표시가 박힌 본문 | 위치 번호만. 예: `["①","②","③","④","⑤"]` | 위치의 인덱스 |

- `passage_words`는 주어진 글·문장을 포함해서 셉니다.
- `insertion`의 `distractor_notes`에는 각 오답 위치에 넣으면 왜 어긋나는지(지시어의 대상이 없음, 뒤 문장과 연결 끊김 등)를 적습니다.
- `insertion`의 위치 표시는 `option_marker`와 무관하게 원본 표기를 따릅니다.

## 단어집 항목 (`vocab_entries[]`)

```json
{
  "word": "sustain",
  "pos": "v.",
  "meaning_ko": "지속하다, 유지하다",
  "example": "The soil cannot sustain crops without water.",
  "derived": ["sustainable (a.)", "sustainability (n.)"]
}
```

| 필드 | 필수 | 설명 |
| :- | :- | :- |
| `word` | 예 | 표제어 (원형) |
| `pos` | 예 | 품사 약어 |
| `meaning_ko` | 예 | 한국어 뜻, 쉼표로 2개까지 |
| `example` | 예 | 예문 한 문장. 원본 지문 문장을 그대로 쓰지 않음 |
| `derived` | 아니오 | 파생어 |

## 원본과 생성 결과의 "비슷함" 판정

`format` 모드에서 생성 JSON은 원본 JSON과 다음이 같아야 합니다.

| 항목 | 기준 |
| :- | :- |
| `items` 길이 | 동일 |
| `option_marker` | 동일 |
| `passage_group` 묶음 구조 | 동일 (어느 문항끼리 지문을 공유하는지) |
| 각 문항의 `type`, `subtype` | 동일 (순서 포함) |
| 각 문항의 `options` 길이 | 동일 |
| 각 문항의 `points` | 동일 |
| `level` | 같거나 한 단계 이내 |
| `passage_words` | 원본의 ±20% |
| `topic_tags` | 1개 이상 겹치거나, 사용자가 다른 소재를 요청한 경우 무시 |

`validate_schema.py --compare source.json generated.json`이 이 표를 검사합니다.
