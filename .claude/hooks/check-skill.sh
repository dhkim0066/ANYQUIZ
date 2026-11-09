#!/bin/bash
# PostToolUse(Edit|Write): 스킬 파일이 바뀌면 검증·컴파일·회귀 테스트를 돌린다.
# 실패 시 exit 2 → Claude에게 stderr가 전달되어 고치게 한다.
input=$(cat)
path=$(echo "$input" | jq -r '.tool_input.file_path // empty')
case "$path" in
  */skills/anyquiz-english/*) ;;
  *) exit 0 ;;
esac
root=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
cd "$root" || exit 0
fail=0
if command -v agentskills >/dev/null 2>&1; then
  agentskills validate skills/anyquiz-english >/tmp/anyquiz-validate.log 2>&1 || { cat /tmp/anyquiz-validate.log >&2; fail=1; }
fi
for f in skills/anyquiz-english/scripts/*.py; do
  python3 -m py_compile "$f" 2>>/tmp/anyquiz-compile.log || { echo "컴파일 실패: $f" >&2; cat /tmp/anyquiz-compile.log >&2; fail=1; }
done
python3 skills/anyquiz-english/scripts/validate_schema.py eval/samples/sample-generated.json >/tmp/anyquiz-reg.log 2>&1 \
  || { echo "회귀 테스트 실패 (eval/samples):" >&2; cat /tmp/anyquiz-reg.log >&2; fail=1; }
lines=$(wc -l < skills/anyquiz-english/SKILL.md)
if [ "$lines" -gt 500 ]; then echo "SKILL.md가 ${lines}줄. 500줄을 넘으면 references/로 옮기세요." >&2; fail=1; fi
rm -f /tmp/anyquiz-*.log
[ "$fail" = 1 ] && exit 2
exit 0
