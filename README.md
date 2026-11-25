# ANYQUIZ

본인이 만든 영어 문제지를 넣으면 **같은 형식의 새 문제**를, 영어 지문을 넣으면 **그 지문 기반 문제**를 만들어 주는 Agent Skill입니다. 교사·강사·학습자가 자기 자료로 학습·출제용 변형 문제를 만드는 용도입니다. Claude Code, claude.ai, Codex CLI 등 [Agent Skills](https://agentskills.io) 표준을 읽는 도구에서 동작합니다.

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

1. 분석: 원본의 형식을 JSON(`references/schema.md`)으로 적고 사용자에게 요약 표로 확인. 정답지가 없는 문제지도 받음
2. 생성: JSON을 제약 조건 삼아 새 문항 작성. 원본 문장은 재사용하지 않음
3. 검증: 형식 비교와 중복률은 스크립트로, 정답은 정답 없는 문제지만 가지고 다시 풀어 확인. 답이 다르거나 둘 이상 가능하면 다시 만들고, 두 번 고쳐도 남는 문항은 "검토 필요 문항"으로 표시해 내보냄
4. 출력: 문제지 / 정답·해설 분리 마크다운, 요청 시 DOCX

## 스크립트 (Python 3)

```bash
pip install pdfplumber pypdf jsonschema python-docx skills-ref
python3 scripts/extract.py exam.pdf out.txt
python3 scripts/validate_schema.py source.json            # 원본 분석: 구조만 검사
python3 scripts/validate_schema.py --stats source.json    # 지문 단어 수, 문단 수, 문장 평균 길이, 보기 길이
python3 scripts/validate_schema.py --compare source.json generated.json
python3 scripts/pick_names.py 8 --avoid source.txt        # 새 지문에 쓸 인물 이름 뽑기 (원본의 이름 제외)
python3 scripts/validate_schema.py --words-in input.txt generated.json   # 단어집의 단어가 입력 글에 있는지
python3 scripts/overlap.py source.txt generated.json      # 원본과 겹치는 정도
python3 scripts/overlap.py run-a.json run-b.json          # 두 실행끼리 겹치는 정도
python3 scripts/render_md.py generated.json out.md
python3 scripts/render_md.py generated.json paper.md --paper-only   # 정답 없이 문제지만
python3 scripts/export_docx.py generated.json out.docx
```

## 알려진 한계

- 어법, 서술형 영작처럼 지원 유형(빈칸·단어집·독해)이 아닌 문항이 섞인 문제지도 받습니다. 그 문항도 만들지만 작성 규칙과 검사가 없으므로, 출력 맨 위에 "지원 범위 밖 문항"으로 번호를 표시합니다. 쓰기 전에 직접 확인하세요.
- 영어만 지원합니다. 다른 과목은 `references/subject-<name>.md`를 추가하면 확장 가능하지만 검증되지 않았습니다.
- 2단 편집 PDF는 텍스트 순서가 섞일 수 있습니다.
- 지문에 실존 인물·수치를 쓰지 않도록 규칙을 두었지만, 모델 생성물이므로 사실 관계를 보장하지 않습니다. 출제 전 검토하세요.

## 이용 안내

이 스킬은 **본인에게 권리가 있거나 이용이 허락된 자료**로 학습·출제용 변형 문제를 만드는 도구입니다. 타인의 저작물을 복제하거나 재배포하는 용도로 사용하지 마십시오.

- 올린 문제지·지문은 사용자의 Claude 세션 안에서만 처리되며, 이 스킬은 파일을 저장하거나 외부로 보내지 않습니다.
- `format` 모드는 원본 문장을 재사용하지 않도록 중복률 검사(6-gram, 15%)를 거칩니다. 그래도 생성물은 모델 출력이므로 **정답과 사실 관계를 검토한 뒤** 사용하세요.
- 생성물의 검토와 이용에 따른 책임은 사용자에게 있습니다.

## 라이선스

MIT
