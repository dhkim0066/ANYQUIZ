#!/bin/bash
# Stop: 스킬 파일이 바뀌었는데 측정 기록이 없으면 알린다. 차단하지 않는다.
root=$(git rev-parse --show-toplevel 2>/dev/null || pwd); cd "$root" || exit 0
changed_skill=$(git status --porcelain skills/anyquiz-english 2>/dev/null | wc -l | tr -d ' ')
changed_results=$(git status --porcelain eval/results 2>/dev/null | wc -l | tr -d ' ')
if [ "$changed_skill" -gt 0 ] && [ "$changed_results" -eq 0 ]; then
  printf '%s\n' '{"systemMessage":"스킬 파일을 수정했지만 eval/results/ 에 새 측정 기록이 없습니다. PLAN.md 라운드 완료 조건을 확인하세요."}'
fi
exit 0
