#!/bin/bash
# PostToolUse(Edit|Write): 스킬 파일이 바뀌면 검증·컴파일·회귀 테스트. 실패 시 exit 2 → Claude가 고친다.
# 의존: bash(Windows는 Git Bash), python3 또는 python. jq 불필요.
. "$(dirname "$0")/_py.sh"
[ -z "$PY" ] && exit 0
input=$(cat)
path=$(printf '%s' "$input" | $PY -c 'import sys,json;print(json.loads(sys.stdin.buffer.read()).get("tool_input",{}).get("file_path","").encode("ascii","backslashreplace").decode())' 2>/dev/null)
case "$path" in *skills/anyquiz-english/*|*skills\\anyquiz-english\\*) ;; *) exit 0 ;; esac
root=$(git rev-parse --show-toplevel 2>/dev/null || pwd); cd "$root" || exit 0
fail=0
if command -v agentskills >/dev/null 2>&1; then
  out=$(agentskills validate skills/anyquiz-english 2>&1) || { echo "$out" >&2; fail=1; }
fi
for f in skills/anyquiz-english/scripts/*.py; do
  out=$($PY -m py_compile "$f" 2>&1) || { echo "컴파일 실패: $f"; echo "$out"; fail=1; } >&2
done
out=$($PY skills/anyquiz-english/scripts/validate_schema.py --compare eval/samples/sample-source.json eval/samples/sample-generated.json 2>&1 \
      && $PY skills/anyquiz-english/scripts/validate_schema.py --compare eval/samples/sample-en-group.source.json eval/samples/sample-en-group.json 2>&1 \
      && $PY skills/anyquiz-english/scripts/validate_schema.py --compare eval/samples/sample-nostem.source.json eval/samples/sample-nostem.json 2>&1 \
      && $PY skills/anyquiz-english/scripts/validate_schema.py --compare eval/samples/sample-mixed.source.json eval/samples/sample-mixed.json 2>&1 \
      && $PY skills/anyquiz-english/scripts/render_md.py eval/samples/sample-mixed.json 2>&1 >/dev/null \
      && $PY skills/anyquiz-english/scripts/render_md.py eval/samples/sample-generated.json 2>&1 >/dev/null) \
  || { echo "회귀 테스트 실패 (eval/samples):"; echo "$out"; fail=1; } >&2
lines=$(wc -l < skills/anyquiz-english/SKILL.md | tr -d ' ')
[ "$lines" -gt 500 ] && { echo "SKILL.md가 ${lines}줄. 500줄을 넘으면 references/로 옮기세요." >&2; fail=1; }
[ "$fail" = 1 ] && exit 2
exit 0
