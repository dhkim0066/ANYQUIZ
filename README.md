# ANYQUIZ

영어 문제지를 넣으면 **같은 형식의 새 문제**를, 영어 지문을 넣으면 **그 지문 기반 문제**를 만들어 주는 Agent Skill입니다. Claude Code, claude.ai, Codex CLI 등 [Agent Skills](https://agentskills.io) 표준을 읽는 도구에서 동작합니다.

> 상태: v0.1 (개발 중). 정확도 검증 전입니다. `PLAN.md`의 로드맵을 참고하세요.

## 할 수 있는 것

| 유형 | 설명 |
| :- | :- |
| 영단어 빈칸 (cloze) | 문맥 단서가 있는 빈칸 문제. 한 칸 / 여러 칸 / 보기 상자 |
| 단어집 (vocab) | 지문에서 수준에 맞는 단어 추출, 또는 수준·주제만으로 생성. 품사·뜻·새 예문 |
| 독해 (reading) | 요지·제목·빈칸 추론·일치·순서·삽입·무관한 문장·요약 |

모드:
- `format`: 올린 문제지와 같은 유형·문항 수·수준·소재로 새 문제
- `passage`: 올린 지문으로 문제 생성 (지문은 결과에 그대로 포함)
- `vocab`: 단어집만

## 설치

### Claude Code

```bash
git clone https://github.com/<owner>/ANYQUIZ.git
mkdir -p .claude/skills
ln -s "$(pwd)/ANYQUIZ/skills/anyquiz-english" .claude/skills/anyquiz-english
```

세션에서 `/anyquiz-english` 또는 자연어("이 문제지와 비슷한 문제 10개 만들어 줘")로 호출합니다.

### claude.ai

`skills/anyquiz-english` 폴더를 zip으로 압축한 뒤 **Customize > Skills > + > Upload a skill**로 올립니다. 코드 실행 기능이 켜져 있어야 합니다.

### Codex CLI

```bash
mkdir -p .agents/skills
cp -r ANYQUIZ/skills/anyquiz-english .agents/skills/
```

## 입력 형식

- 텍스트 기반 PDF, 붙여넣은 텍스트, `.txt`/`.md`
- **스캔 이미지 PDF는 지원하지 않습니다.** 텍스트 추출이 안 되면 그렇게 알려 줍니다.

## 동작 방식

1. 분석: 원본을 문항 JSON(`references/schema.md`)으로 변환하고 사용자에게 요약 표로 확인
2. 생성: JSON을 제약 조건 삼아 새 문항 작성. 원본 문장은 재사용하지 않음
3. 검증: 원본을 보지 않은 상태로 다시 풀어 정답 일치 확인 → 스키마·중복률 스크립트
4. 출력: 문제지 / 정답·해설 분리 마크다운, 요청 시 DOCX

## 스크립트 (Python 3)

```bash
pip install pdfplumber pypdf jsonschema python-docx
python3 scripts/extract.py exam.pdf out.txt
python3 scripts/validate_schema.py generated.json
python3 scripts/validate_schema.py --compare source.json generated.json
python3 scripts/overlap.py source.txt generated.json
python3 scripts/export_docx.py generated.json out.docx
```

## 알려진 한계

- 영어만 지원합니다. 다른 과목은 `references/subject-<name>.md`를 추가하면 확장 가능하지만 검증되지 않았습니다.
- 2단 편집 PDF는 텍스트 순서가 섞일 수 있습니다.
- 지문에 실존 인물·수치를 쓰지 않도록 규칙을 두었지만, 모델 생성물이므로 사실 관계를 보장하지 않습니다. 출제 전 검토하세요.

## 저작권

올린 문제지·지문의 권리와 사용 책임은 사용자에게 있습니다. `format` 모드는 원본 문장을 재사용하지 않도록 중복률 검사(6-gram, 15%)를 거치지만, 생성물의 최종 확인은 사용자 몫입니다.

## 라이선스

MIT
