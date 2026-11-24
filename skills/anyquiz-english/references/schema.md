# 문항 JSON 스키마 (v2)

문제지 한 장을 JSON 하나로 적습니다. 같은 구조를 두 가지 역할로 씁니다.

| `role` | 무엇을 적는가 | 필수 범위 |
| :- | :- | :- |
| `source` | 원본 문제지를 **분석한** 결과 | 형식 정보만. 원본에 없는 것(오답 이유, 해설, 예문)은 **지어 넣지 않습니다** |
| `generated` | 새로 **만든** 문제지 | 형식 정보 + 정답 + 해설 + 오답 이유 |

두 JSON을 나란히 비교하면 "형식이 같은가"가 코드로 판정됩니다. 기계 검증용 정의는 `scripts/exam.schema.json`에 있고, 역할별 필수 항목과 작성 규칙은 `scripts/validate_schema.py`가 검사합니다.

**세지 말고 스크립트에 맡깁니다.** 지문 단어 수, 보기 길이, 문장 평균 길이는 JSON에 적지 않습니다. `validate_schema.py --stats file.json`이 계산해 보여 줍니다.

## 최상위

```json
{
  "schema_version": 2,
  "role": "source",
  "answer_key": "provided",
  "title": "중학교 1학년 내신 영어 연습지",
  "mode": "format",
  "language": "ko",
  "explanation_language": "ko",
  "option_marker": "circled",
  "source_level": "A2",
  "sections": [
    {"title": "Ⅰ. 독해", "first": 1, "last": 6},
    {"title": "Ⅱ. 빈칸", "first": 7, "last": 9},
    {"title": "Ⅲ. 어휘", "first": 10, "last": 10}
  ],
  "items": [ ... ]
}
```

| 필드 | 값 | 필수 | 설명 |
| :- | :- | :- | :- |
| `schema_version` | `2` | 예 | |
| `role` | `source` \| `generated` | 예 | 위 표 |
| `answer_key` | `provided` \| `solved` \| `none` | source만 예 | 원본 정답의 출처. `provided`: 원본에 정답지가 있었음. `solved`: 정답지가 없는데 사용자가 원본의 답도 풀어 달라고 해서 분석 단계가 직접 풂. `none`: 정답을 적지 않음. **새 문제를 만드는 데 원본 정답은 필요 없으므로 `none`이어도 진행합니다** |
| `title` | 문자열 | 예 | 문제지 제목. `format` 모드의 생성물은 원본 제목을 그대로 씁니다 |
| `mode` | `format` \| `passage` \| `vocab` | 예 | |
| `language` | `ko` \| `en` | 예 | **발문** 언어 |
| `explanation_language` | `ko` \| `en` | 아니오 | 해설 언어. 없으면 `language`와 같음. 영어 발문에 한국어 해설인 문제지는 `language: en`, `explanation_language: ko` |
| `option_marker` | `circled` \| `letter` \| `number` | 예 | 보기 번호 표기. ①②③ / (A)(B)(C) / (1)(2)(3). `format` 모드는 원본 그대로. 원본이 없으면 사용자 지정, 없으면 `circled` |
| `source_level` | `A1` `A2` `A2+` `B1` `B1+` `B2` `B2+` `C1` `C2` | 예 | 전체 수준 |
| `sections` | 배열 | 아니오 | 영역(Part) 구분. 원본에 영역 제목이 있으면 적습니다. 문항 전체를 빠짐없이, 겹치지 않게, 순서대로 덮어야 합니다 |
| `items` | 배열 | 예 | 문항. 1개 이상 |
| `review` | 배열 | 아니오 (generated만) | 검증에서 두 번 고친 뒤에도 지적이 남은 문항. `[{"id": 6, "reason": "…"}]`. 출력 맨 위에 "검토 필요 문항"으로 찍힙니다 |

`sections[]`의 항목: `title`(영역 제목, 원본 그대로), `instruction`(영역 공통 지시문, 선택), `first`·`last`(그 영역의 첫·마지막 문항 번호).

**안내문을 어디에 적는가.** 영역 제목 바로 아래에서 그 영역의 문항 전체에 걸리는 지시문은 `sections[].instruction`입니다(예: `Choose the best word for each blank.`, `[9~12] 다음 글의 빈칸에…`). 지문 하나에 딸린 문항들 위의 안내문은 `group_instruction`입니다(예: `[1~3] 다음 글을 읽고 물음에 답하시오.`). 한 문장이 두 일을 겸하면 `sections[].instruction`에 한 번만 적습니다. `format` 모드의 출력은 적힌 안내문만 찍고, 원본에 없던 묶음 안내문을 만들어 붙이지 않습니다. 안내문에 든 배점 문구(`각 4점`)는 원본 그대로 두고, 숫자는 `points`에도 적습니다.

출력할 때 이름·날짜·점수 줄과 영역별 배점표는 스크립트가 `sections`와 `points`에서 만듭니다. JSON에 따로 적지 않습니다.

## 문항 공통 필드

| 필드 | 타입 | source | generated | 설명 |
| :- | :- | :- | :- | :- |
| `id` | 정수 | 예 | 예 | 1부터 순번 |
| `type` | `cloze` \| `vocab` \| `reading` | 예 | 예 | |
| `subtype` | 아래 표 | 예 | 예 | |
| `level` | 수준 값 | 예 | 예 | 문항 수준 |
| `points` | 숫자 | 예 | 예 | 문항 전체 배점. 배점이 없으면 0 |
| `points_per_part` | 숫자 | 해당 시 | 해당 시 | 짝·빈칸마다 부분 점수를 주는 문항의 단위 배점 (예: 8쌍 × 2점이면 2) |
| `topic_tags` | 문자열 배열 | 예 | 예 | 소재 태그 1~4개. 영어 소문자와 숫자, 낱말 사이는 하이픈(`school-club`). 공백은 쓰지 않습니다. 지문이 **무엇에 관한 글인지**를 한두 낱말로 적습니다(`community-garden`). 줄거리나 결론은 적지 않습니다. 지문이 없는 어휘 문항은 `["vocabulary"]` |
| `stem` | 문자열 | 아래 참고 | 아래 참고 | 발문. **`format` 모드는 원본 발문을 그대로** 씁니다. 번호와 배점 표기는 넣지 않습니다 |
| `passage` | 문자열 | 유형별 | 유형별 | 지문. 문단은 빈 줄로 나눕니다 |
| `given` | 문자열 | 유형별 | 유형별 | 순서 문항의 "주어진 글", 삽입 문항의 "주어진 문장" |
| `prompt_text` | 문자열 | 아니오 | 아니오 | 발문 아래, 보기 위에 놓이는 글. 요약문 문항의 요약문 등 |
| `footnote` | 문자열 | 아니오 | 아니오 | 지문 아래 각주. 예: `*bean: 콩` |
| `passage_group` | 문자열 | 해당 시 | 해당 시 | 지문 하나에 문항이 여러 개 딸릴 때의 묶음 이름(예: `g1`). 같은 묶음은 `passage`·`footnote`가 글자까지 같고 번호가 이어져야 합니다 |
| `group_instruction` | 문자열 | 아니오 | 아니오 | 묶음 지문 위의 안내문(원본 그대로). 묶음의 **첫 문항에만** 적습니다. 예: `[1~3] 다음 글을 읽고 물음에 답하시오.` |
| `options` | 문자열 배열 | 객관식 | 객관식 | 보기. 번호 표기는 넣지 않습니다 |
| `option_language` | `ko` \| `en` | 객관식 | 객관식 | **보기** 언어. 한국어 발문에 영어 보기인 문항은 `en`. 보기가 위치·순서 기호뿐인 유형(`order`, `insertion`, `irrelevant`)은 생략 |
| `polarity` | `match` \| `mismatch` | `detail`만 | `detail`만 | "일치하는 것"이면 `match`, "일치하지 않는 것"이면 `mismatch` |
| `answer` | 유형별 | `answer_key`가 `none`이 아니면 | 예 (`word-list`, `meaning-write` 제외) | 아래 "유형별 담는 법" |
| `explanation` | 문자열 | 아니오 | 예 (`word-list`, `meaning-write` 제외) | 해설 두 문장 이내. 원본에 해설이 있을 때만 source에 적습니다 |
| `distractor_notes` | 문자열 배열 | 아니오 | 아래 참고 | 정답이 아닌 보기마다 한 구절, **보기 순서대로**(정답은 건너뜀). 길이 = 보기 수 − 1. 보기 번호는 쓰지 않습니다(스크립트가 붙임) |
| `words_from_passages` | `true` \| `false` | 해당 시 | 해당 시 | 단어집·뜻 쓰기·짝짓기의 단어가 같은 문제지의 지문에서 나온 것인지. 아래 "단어 항목" 절 |

**밑줄과 굵게.** 발문이 "밑줄 친", "underlined"라고 하는 대상은 `__…__`로, "굵게 표시한"이라고 하는 대상은 `**…**`로 감쌉니다(지칭 추론의 `__it__`, 함축 의미의 인용문). 원본에 ⓐ 같은 기호가 있으면 `ⓐ __it__`처럼 기호를 앞에 둡니다. 원본이 없는 모드에서는 대상이 하나면 기호 없이 `__it__`만 쓰고(발문: `밑줄 친 it이 가리키는 것은?`), 한 지문에 대상이 둘 이상일 때만 ⓐ, ⓑ를 붙입니다. 출력할 때 `__…__`는 실제 밑줄이 됩니다. PDF에서는 표시가 사라지므로 발문의 말을 보고 정합니다. 발문은 밑줄인데 표시가 `**…**`뿐이면 검증기가 실패로 봅니다.

**각주.** `footnote`에 원본 표기 그대로 적습니다(`*bean: 콩`). 각주는 지문 내용에 달린 것이라 형식 비교 대상이 아닙니다. 생성물에는 새 지문에 수준을 넘는 낱말이 있을 때만 답니다.

**빈칸.** 밑줄 네 개(`____`)로 적습니다. 원본의 빈칸 길이는 옮기지 않습니다.

**발문(`stem`)을 생략하는 경우.** 원본에 문항별 발문이 없으면 비워 둡니다. 없는 발문을 지어 넣거나 영역 지시문을 복사해 넣지 않습니다. 검증기는 다음 중 하나일 때 생략을 받습니다.

- `type`이 `cloze`인 문항
- 그 문항이 속한 영역에 `sections[].instruction`이 있음
- 그 문항이 속한 묶음의 첫 문항에 `group_instruction`이 있음
- `word-list` (단어집 표에는 발문이 없는 것이 보통)

**발문에 지문 내용이 박혀 있는 경우.** 발문 안의 인용문·대명사·표현(`밑줄 친 "a quiet storm"이 뜻하는 것은?`)은 새 지문의 해당 표현으로 바꿉니다. 나머지 문구는 원본 그대로 둡니다.

**`distractor_notes`를 쓰는 문항.** 보기가 문장·구·낱말인 독해 객관식(`reading`에서 `order`, `insertion`, `irrelevant`를 뺀 전부)의 생성물에는 필수입니다. 보기가 기호뿐인 세 유형과 `cloze` 객관식에는 쓰지 않아도 됩니다(해설로 충분). 불일치(`polarity: mismatch`) 문항에서는 정답이 아닌 보기, 곧 지문과 일치하는 보기마다 지문의 어디와 맞는지를 적습니다.

## subtype

| type | subtype | 설명 |
| :- | :- | :- |
| `cloze` | `single-blank` | 빈칸 하나, 보기는 **단어**(한두 낱말). 연결어 빈칸 포함 |
| `cloze` | `multi-blank` | (A)(B)(C) 각 자리의 낱말을 고르는 조합 |
| `cloze` | `word-bank` | 보기 상자에서 골라 쓰기 (주관식) |
| `vocab` | `word-list` | 학습용 단어집 표 |
| `vocab` | `meaning-write` | 단어의 뜻 쓰기 (주관식) |
| `vocab` | `synonym-match` | 유의어 짝짓기 |
| `vocab` | `definition-match` | 뜻풀이 짝짓기 |
| `reading` | `main-idea` | 요지·주제 |
| `reading` | `title` | 제목 |
| `reading` | `blank-inference` | 빈칸 추론. 보기는 **구·절** |
| `reading` | `detail` | 내용 일치·불일치 (`polarity` 필수) |
| `reading` | `reference` | 지칭 추론 |
| `reading` | `implied-meaning` | 함축 의미 |
| `reading` | `inference` | 내용 추론 |
| `reading` | `order` | 글의 순서 |
| `reading` | `insertion` | 문장 삽입 |
| `reading` | `irrelevant` | 흐름과 무관한 문장 |
| `reading` | `summary` | 요약문 완성 |

**빈칸 문제의 분류 기준.** 영역 제목이 아니라 보기를 봅니다. 보기 낱말 수의 중앙값이 2 이하면 `cloze/single-blank`, 3 이상이면 `reading/blank-inference`입니다. 검증기가 이 기준으로 검사합니다.

새 subtype이 필요하면 이 표와 아래 규약 표에 먼저 추가하고 `question-types.md`에 규칙을 씁니다.

## 유형별 담는 법

유형마다 무엇을 어느 필드에 담는지 고정합니다. 실행마다 다르게 담기면 형식 비교와 출력이 깨집니다.

| subtype | `passage` | 그 밖의 필드 | `options` | `answer` |
| :- | :- | :- | :- | :- |
| 일반 객관식 (main-idea, title, detail, reference, implied-meaning, inference, blank-inference) | 지문 | | 보기 문장 | 정답 보기의 인덱스(0부터) |
| `summary` | 지문 | `prompt_text`: 빈칸 `(A) ____`, `(B) ____`가 든 요약문. 원본이 없고 보기 표기가 `letter`면 보기 번호와 겹치므로 `(1) ____`, `(2) ____` | 조합. 예: `"bottles – sounds"` | 인덱스 |
| `single-blank` (단독) | 빈칸 `____`이 든 문장·단락 | | 단어 | 인덱스 |
| `single-blank` (한 지문에 번호 빈칸 여러 개) | 빈칸마다 `(문항번호) ____`. 예: `(11) ____` | `passage_group`으로 묶음 | 단어 | 인덱스 |
| `multi-blank` | 자리마다 `(A)【umbrella / notebook】` 또는 `(A) ____` | | 조합. 자리 구분은 ` – `. 예: `"umbrella – close – dry"` | 인덱스 |
| `word-bank` | 빈칸마다 `____`. 원본에 `(가)` 같은 라벨이 있으면 `(가) ____` | `word_bank`: 보기 상자의 낱말 배열 | 없음 | **빈칸 순서대로 낱말 배열**. 예: `["nose","scarf","hat","arms"]` |
| `order` | `(A) …`, `(B) …`, `(C) …` 단락을 문제지에 나온 순서대로, 빈 줄로 구분 | `given`: 주어진 글 | 순서 조합. 구분은 `-`. 예: `"(B)-(C)-(A)"` | 인덱스 |
| `insertion` | `( ① )`~`( ⑤ )` 위치 표시가 박힌 본문 | `given`: 주어진 문장 | 위치 기호만. 예: `["①","②","③","④","⑤"]` | 인덱스 |
| `irrelevant` | 문장 앞에 `①`~`④` 번호가 붙은 본문 | | 번호 기호만 | 인덱스 |
| `synonym-match`, `definition-match` | 없음 | `match_left`: 왼쪽 낱말 배열. `match_right`: 오른쪽 배열(오답을 섞어 더 길어도 됨). `match_left_labels`·`match_right_labels`: 원본의 기호를 괄호·마침표까지 그대로(예: `["(가)","(나)"]`, `["A.","B."]`), 선택 | 없음 | **`match_left` 순서대로 `match_right`의 인덱스 배열**. 예: `[5,7,2]` |
| `word-list` | 없음 | `vocab_entries`, `vocab_columns` | 없음 | 없음 |
| `meaning-write` | 없음 | `vocab_entries` (`word`와 `meaning`) | 없음 | 없음. 정답은 각 항목의 `meaning` |

- 보기가 위치·번호 기호뿐인 `insertion`·`irrelevant`는 출력할 때 보기 목록을 찍지 않습니다. 기호가 이미 지문 안에 있기 때문입니다.
- 짝짓기 유형에 `vocab_entries`를 쓰지 않습니다. 쓰면 문제지에 뜻이 함께 찍혀 답이 드러납니다.
- `word-list`는 문항 번호 없이 출력됩니다. 배점이 없으면 `points: 0`.

## 단어 항목 (`vocab_entries[]`)

```json
{"word": "sustain", "pos": "v.", "meaning": "지속하다, 유지하다", "example": "The soil cannot sustain crops without regular rain."}
```

| 필드 | 설명 |
| :- | :- |
| `word` | 표제어(기본형). 항상 필수 |
| `pos` | 품사. `format` 모드는 원본 단어집의 표기를 따름(`v.`, `동사` 등). 원본이 없는 모드는 `n.` `v.` `adj.` `adv.` |
| `meaning` | 뜻. 원본이 한국어 뜻이면 한국어, 영어 뜻풀이면 영어 |
| `example` | 예문. 원본 지문의 문장을 그대로 쓰지 않음 |
| `derived` | 파생어 배열 |

`vocab_columns`는 표에 나오는 열을 순서대로 적습니다. 값은 `word`, `pos`, `meaning`, `example`, `derived` 중에서 고릅니다. **원본에 없는 열을 생성물에 더하지 않습니다.** 원본 단어집이 단어·품사·뜻 세 열이면 생성물도 세 열입니다.

`words_from_passages: true`는 "이 문항의 단어는 같은 문제지의 지문에 나온 것"이라는 제약입니다. "지문"은 같은 문제지의 다른 문항에 있는 지문·주어진 글·요약문·보기를 모두 포함하고, 활용형(sought ← seek)으로 나온 것도 인정합니다. 원본이 그렇다면 source에 적고, 생성물은 **새로 쓴 지문**에서 단어를 뽑습니다. 검증기가 실제로 지문에 있는지 확인합니다.

## 원본과 생성물의 형식 비교

`validate_schema.py --compare source.json generated.json`이 다음을 검사합니다.

| 항목 | 기준 |
| :- | :- |
| `language`, `option_marker` | 동일 |
| `sections` | 개수, 제목, 문항 범위 동일 |
| 문항 수 | 동일 |
| 문항별 `type`, `subtype` | 동일 (순서 포함) |
| 문항별 보기 수, `option_language`, `polarity` | 동일 |
| 문항별 `points`, `points_per_part` | 동일 |
| 문항별 수준 | 두 칸 이내 (예: B1 ↔ B2는 허용, A2 ↔ B2는 불가) |
| 지문 단어 수 (`given` 포함, 스크립트가 셈) | 원본의 ±20%. 짧은 지문은 ±5단어까지 허용 |
| 지문의 문장 평균 길이 (세 문장 이상인 지문) | 원본의 ±25%. 벗어나면 실패가 아니라 **주의** |
| `passage_group` 묶음 구조 | 동일 |
| 짝짓기의 좌·우 항목 수와 기호 | 동일 |
| `word_bank` 낱말 수와 빈칸 수 | 동일 |
| 단어 항목 수, `vocab_columns`, `words_from_passages` | 동일 |
| `topic_tags` | 1개 이상 겹침 (사용자가 다른 소재를 요청했으면 무시) |

정답 위치, 지문 내용, 보기 내용은 비교하지 않습니다. 그것은 달라야 하는 부분입니다.

## 생성물에만 적용하는 작성 규칙

원본은 고칠 수 없는 기준이므로 아래 검사는 `role: generated`에만 적용합니다.

- 보기 길이 균형: 가장 긴 보기가 가장 짧은 보기의 2배를 넘으면서 3단어 이상 차이 나면 실패
- 정답만 3단어 이상 길거나 짧으면 실패
- 객관식이 5문항 이상일 때 같은 정답 번호가 40%를 넘으면 실패
- `multi-blank`: 자리마다 보기 전체에 서로 다른 낱말이 두 가지 이상 나와야 함 (한 자리가 모든 보기에서 같으면 그 자리는 검사되지 않음)
- `definition-match`: 뜻풀이에 그 낱말 자체를 쓰지 않음
- `word-list`의 예문(예문 열이 있을 때)은 6단어 이상
- `reference`·`implied-meaning`: 지문에 대상 표시(`__…__`, `**…**`, ⓐ류 중 하나)가 있어야 함
- `meaning-write`: 단어의 정답 뜻이 같은 문제지의 한국어 보기에 그대로 나오거나, 그 단어가 각주에 풀이돼 있으면 실패 (답이 문제지에 적혀 있는 셈)
- 오답 두 개 이상에만 절대 표현(always, never, only, 반드시, 절대 등)이 있고 정답에는 없으면 **주의** (표현만 보고 지울 수 있음). every, all, 모든은 평범한 뜻으로 자주 쓰여 보지 않습니다
- `review`의 문항 번호는 실제 문항이어야 함

"지문 없이 보기만 봐도 풀리는가"는 검사하지 않습니다. 이 스킬을 시험할 때 사람이 만든 원본 문제지도 지문을 빼고 거의 다 풀려서, 문항을 가르는 기준이 되지 못했습니다.
