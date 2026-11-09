# 공용: python 실행 파일 찾기 (Windows는 보통 python, macOS/Linux는 python3)
if command -v python3 >/dev/null 2>&1; then PY=python3
elif command -v python >/dev/null 2>&1; then PY=python
else PY=""; fi
