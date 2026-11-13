#!/usr/bin/env python3
"""Check whether Atelje 212 has published its December repertoire.

Calls the same endpoint the repertoar page uses (POST qrydata.php, q=1)
and counts real shows for the given month.

Exit codes: 0 = shows found, 1 = still empty, 2 = check broken
(request failed or the response no longer looks like a show list).

Env:
  NTFY_TOPIC   push notifications via https://ntfy.sh/<topic>
  YEAR, MONTH  month to watch (default 2026-12)
  STATE_FILE   optional; once shows are found this file is created and
               later runs exit 0 silently (used by the local launchd job)
"""
import datetime as dt
import json
import os
import sys
import urllib.parse
import urllib.request

YEAR = int(os.environ.get("YEAR", "2026"))
MONTH = int(os.environ.get("MONTH", "12"))
URL = "https://bilet.atelje212.rs/qrydata.php"
PAGE = "https://bilet.atelje212.rs/repertoar.php"
STATE_FILE = os.environ.get("STATE_FILE")


class CheckBroken(Exception):
    pass


def fetch_month(year: int, month: int) -> list[dict]:
    body = urllib.parse.urlencode({
        "q": 1, "godina": year, "mesec": month, "dan": 1,
        "sdsp": 1,  # only dates with events
        "sap": 1,   # only active events
        "ss": 0, "trazi": "", "user_tipid": "",
        "tip_prikaza": 0, "program": 0,
    }).encode()
    req = urllib.request.Request(
        URL, data=body, method="POST",
        headers={
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
            "User-Agent": "Mozilla/5.0 (repertoire watcher)",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read().decode("utf-8")
    except Exception as e:
        raise CheckBroken(f"request failed: {e}") from e
    try:
        data = json.loads(raw)
    except ValueError as e:
        raise CheckBroken(f"response is not JSON: {raw[:120]!r}") from e
    shows = data.get("resp") if isinstance(data, dict) else None
    if not isinstance(shows, list):
        raise CheckBroken(f"unexpected response shape: {raw[:120]!r}")
    if shows and not all(isinstance(s, dict) and "datum" in s and "predstava" in s
                         for s in shows):
        raise CheckBroken("show entries no longer have datum/predstava fields")
    # Skip "Nema događaja" placeholders and anything outside the month.
    prefix = f"{year}-{month:02d}"
    return [s for s in shows
            if str(s.get("datum", "")).startswith(prefix)
            and s.get("online_prodaja") is not None]


def notify(title: str, msg: str, priority: str, tags: str) -> None:
    topic = os.environ.get("NTFY_TOPIC")
    if not topic:
        return
    req = urllib.request.Request(
        f"https://ntfy.sh/{topic}", data=msg.encode("utf-8"), method="POST",
        headers={"Title": title, "Click": PAGE, "Priority": priority, "Tags": tags},
    )
    try:
        urllib.request.urlopen(req, timeout=15)
    except Exception as e:
        print(f"ntfy failed: {e}", file=sys.stderr)


def main() -> int:
    if STATE_FILE and os.path.exists(STATE_FILE):
        print("Already found earlier; nothing to do.")
        return 0

    try:
        shows = fetch_month(YEAR, MONTH)
    except CheckBroken as e:
        print(f"CHECK BROKEN: {e}", file=sys.stderr)
        # Alert at most once an hour (runs every ~10 min), so an outage
        # doesn't spam the phone.
        if dt.datetime.now(dt.timezone.utc).minute < 10:
            notify("Atelje 212 checker is failing", str(e)[:300],
                   priority="default", tags="warning")
        return 2

    if not shows:
        print(f"{YEAR}-{MONTH:02d}: no shows published yet.")
        return 1

    lines = [f"{s['datum']} {str(s.get('vreme', ''))[:5]}  {str(s['predstava']).strip()}"
             for s in shows]
    summary = f"{len(shows)} shows published for {YEAR}-{MONTH:02d}"
    print(summary)
    print("\n".join(lines))
    notify("Atelje 212: December repertoire is out!",
           summary + "\n" + "\n".join(lines[:10]),
           priority="urgent", tags="rotating_light,performing_arts")
    if STATE_FILE:
        with open(STATE_FILE, "w") as f:
            f.write(dt.datetime.now().isoformat() + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
