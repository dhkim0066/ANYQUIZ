#!/bin/bash
# PreToolUse(Edit|Write): eval/sources/ 와 eval/holdout/ 은 사람이 만들고 사람만 고친다. Claude가 수정하지 못하게 막는다.
# 입력은 stdin의 바이트를 그대로 읽는다(Windows 한국어 로캘에서도 UTF-8로 해석되게).
. "$(dirname "$0")/_py.sh"
[ -z "$PY" ] && exit 0
$PY -c '
import sys, json, posixpath
try:
    d = json.loads(sys.stdin.buffer.read())
    p = str(d.get("tool_input", {}).get("file_path", ""))
except Exception:
    sys.exit(0)
p = posixpath.normpath(p.replace("\\", "/")).lower()
RULES = (
    ("eval/sources/", "eval/sources/ 는 원본 문제지와 사람이 작성한 기준 자료입니다. 수정이 필요하면 사용자에게 요청하세요."),
    ("eval/holdout/", "eval/holdout/ 은 측정 전용 문제지입니다. 고치지 않습니다. 수정이 필요하면 사용자에게 요청하세요."),
)
for name, why in RULES:
    if ("/" + name) in p or p.startswith(name):
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
            "permissionDecision": "deny", "permissionDecisionReason": why}}))
        break
'
exit 0
