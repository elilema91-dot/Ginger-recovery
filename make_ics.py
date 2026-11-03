#!/usr/bin/env python3
"""강차 회원·일정 → 아이폰 구독용 calendar.ics 생성기.

사용법: python3 make_ics.py events.json members.json > calendar.ics
 - events.json : 아티팩트 db 'events' 문서 목록 [{"id":..., "data":{...}}, ...]
 - members.json: 아티팩트 db 'members' 문서 목록 (이름 찾기용)
이벤트 필드: date(YYYY-MM-DD) end? time?(HH:MM) title memberId? cat memo? repeat?("monthly")
"""
import json, sys, datetime as dt

KST = dt.timezone(dt.timedelta(hours=9))

def esc(s):
    return str(s or "").replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")

def fold(line):
    b = line.encode("utf-8")
    out, cur = [], b""
    for ch in line:
        c = ch.encode("utf-8")
        if len(cur) + len(c) > 73:
            out.append(cur); cur = b" " + c
        else:
            cur += c
    out.append(cur)
    return "\r\n".join(x.decode("utf-8") for x in out)

def mask(n):
    n = n or ""
    if len(n) <= 1: return n
    if len(n) == 2: return n[0] + "*"
    return n[0] + "*" * (len(n) - 2) + n[-1]

def load(p):
    d = json.load(open(p, encoding="utf-8"))
    return [(x["id"], x.get("data", x)) for x in d]

GROUPS = {
    "member.ics": ("강차 회원", "#2F6B4F", {"회원"}),
    "riding.ics": ("강차 라이딩", "#C2463B", {"라이딩"}),
    "life.ics":   ("강차 생활", "#E08A2E", None),  # 나머지 전부
}

def main():
    # 사용법2: python3 make_ics.py events.json members.json --split 출력폴더
    if len(sys.argv) > 4 and sys.argv[3] == "--split":
        import io, contextlib, os
        allev = load(sys.argv[1])
        used = set().union(*[g[2] for g in GROUPS.values() if g[2]])
        for fn, (name, color, cats) in GROUPS.items():
            sub = [x for x in allev if (x[1].get("cat") in cats if cats else x[1].get("cat") not in used)]
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                build(sub, sys.argv[2], name, color)
            open(os.path.join(sys.argv[4], fn), "w", encoding="utf-8", newline="").write(buf.getvalue())
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            build(allev, sys.argv[2], "강차 일정", None)
        open(os.path.join(sys.argv[4], "calendar.ics"), "w", encoding="utf-8", newline="").write(buf.getvalue())
        return
    build(load(sys.argv[1]), sys.argv[2], "강차 일정", None)

def build(events, members_path, calname, color):
    events = list(events)
    members = {i: mask(m.get("name", "")) for i, m in load(members_path)}  # 공개 저장소라 이름 가운데 가림
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    L = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//gangcha//calendar//KO",
         "CALSCALE:GREGORIAN", "METHOD:PUBLISH", "X-WR-CALNAME:" + calname,
         "X-WR-TIMEZONE:Asia/Seoul", "REFRESH-INTERVAL;VALUE=DURATION:PT1H",
         "X-PUBLISHED-TTL:PT1H"]
    if color:
        L += ["X-APPLE-CALENDAR-COLOR:" + color, "COLOR:" + color]
    for eid, e in events:
        if not e.get("date"):
            continue
        name = members.get(e.get("memberId") or "", "")
        title = e.get("title") or ""
        summary = (name + (" · " + title if title else "")) if name else title
        y, m, d = map(int, e["date"].split("-"))
        L += ["BEGIN:VEVENT", f"UID:{eid}@gangcha", f"DTSTAMP:{stamp}",
              fold("SUMMARY:" + esc(summary))]
        if e.get("time"):
            hh, mm = map(int, e["time"].split(":"))
            s = dt.datetime(y, m, d, hh, mm, tzinfo=KST).astimezone(dt.timezone.utc)
            f = s + dt.timedelta(hours=1)
            L += ["DTSTART:" + s.strftime("%Y%m%dT%H%M%SZ"), "DTEND:" + f.strftime("%Y%m%dT%H%M%SZ")]
            alarm = "-PT30M"
        else:
            end = e.get("end") or e["date"]
            ey, em, ed = map(int, end.split("-"))
            nxt = dt.date(ey, em, ed) + dt.timedelta(days=1)
            L += [f"DTSTART;VALUE=DATE:{y:04d}{m:02d}{d:02d}", "DTEND;VALUE=DATE:" + nxt.strftime("%Y%m%d")]
            alarm = "-PT15H"  # 전날 오전 9시
        if e.get("repeat") == "monthly":
            L.append(f"RRULE:FREQ=MONTHLY;BYMONTHDAY={d}")
        if e.get("cat"):
            L.append("CATEGORIES:" + esc(e["cat"]))
        if e.get("memo"):
            L.append(fold("DESCRIPTION:" + esc(e["memo"])))
        L += ["BEGIN:VALARM", "ACTION:DISPLAY", fold("DESCRIPTION:" + esc(summary)),
              f"TRIGGER:{alarm}", "END:VALARM", "END:VEVENT"]
    L.append("END:VCALENDAR")
    sys.stdout.write("\r\n".join(L) + "\r\n")

if __name__ == "__main__":
    main()
