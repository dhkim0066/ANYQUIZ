#!/bin/bash
# PreToolUse(Edit|Write): eval/sources/ 는 사람이 만든 기준 데이터. Claude가 수정하지 못하게 막는다.
input=$(cat)
path=$(echo "$input" | jq -r '.tool_input.file_path // empty')
case "$path" in
  */eval/sources/*)
    jq -n '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"deny",
      permissionDecisionReason:"eval/sources/ 는 원본 문제지와 사람이 작성한 기준 JSON입니다. 수정이 필요하면 사용자에게 요청하세요."}}'
    ;;
esac
exit 0
