#!/bin/bash
# PreToolUse(Edit|Write): eval/sources/ 는 사람이 만든 기준 데이터. Claude가 수정하지 못하게 막는다.
. "$(dirname "$0")/_py.sh"
[ -z "$PY" ] && exit 0
HOOK_INPUT=$(cat) $PY -c '
import os, sys, json
try:
    d = json.loads(os.environ.get("HOOK_INPUT", "{}"))
except Exception:
    sys.exit(0)
p = d.get("tool_input", {}).get("file_path", "").replace("\\", "/")
if "/eval/sources/" in p or p.startswith("eval/sources/"):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": "eval/sources/ 는 원본 문제지와 사람이 작성한 기준 JSON입니다. 수정이 필요하면 사용자에게 요청하세요."}},
        ensure_ascii=False))
'
exit 0
