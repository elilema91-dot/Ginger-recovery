#!/usr/bin/env python3
"""강차 일정 동기화 파일(sync.enc) 암호화/복호화.
키는 저장소에 없음 (환경변수 GANGCHA_KEY).
  python3 sync_tool.py pack events.json members.json sync.enc
  python3 sync_tool.py unpack sync.enc out.json   -> {"events":[...], "members":[...]}
"""
import json, os, sys
from cryptography.fernet import Fernet
f = Fernet(os.environ["GANGCHA_KEY"].encode())
if sys.argv[1] == "pack":
    ev = json.load(open(sys.argv[2], encoding="utf-8"))
    mb = json.load(open(sys.argv[3], encoding="utf-8"))
    blob = json.dumps({"events": ev, "members": [{"id": m["id"], "name": m["data"]["name"]} for m in mb]}, ensure_ascii=False)
    open(sys.argv[4], "wb").write(f.encrypt(blob.encode("utf-8")))
else:
    d = json.loads(f.decrypt(open(sys.argv[2], "rb").read()).decode("utf-8"))
    json.dump(d, open(sys.argv[3], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
