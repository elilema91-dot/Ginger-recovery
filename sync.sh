#!/bin/bash
# 채팅에서 일정 바꾼 뒤 실행: ics 3종 + 전체 + 암호화 동기화 파일 생성
# 사용: GANGCHA_KEY=... bash sync.sh events.json members.json
set -e
D=$(cd "$(dirname "$0")" && pwd)
python3 "$D/make_ics.py" "$1" "$2" --split "$D"
python3 "$D/sync_tool.py" pack "$1" "$2" "$D/sync.enc"
