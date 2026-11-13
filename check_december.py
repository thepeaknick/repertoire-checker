#!/usr/bin/env python3
"""Check whether Atelje 212 has published its December repertoire.

Calls the same endpoint the repertoar page uses (POST qrydata.php, q=1)
and counts real shows for the given month. Exit code 0 = shows found,
1 = still empty, 2 = request failed.

Optional push notification: set NTFY_TOPIC (https://ntfy.sh/<topic>).
"""
import json
import os
import sys
import urllib.parse
import urllib.request

YEAR = int(os.environ.get("YEAR", "2026"))
MONTH = int(os.environ.get("MONTH", "12"))
URL = "https://bilet.atelje212.rs/qrydata.php"


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
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read().decode("utf-8"))
    shows = data.get("resp") or []
    # Skip "Nema događaja" placeholders and anything outside the month.
    prefix = f"{year}-{month:02d}"
    return [s for s in shows
            if str(s.get("datum", "")).startswith(prefix)
            and s.get("online_prodaja") is not None]


def notify(title: str, msg: str) -> None:
    topic = os.environ.get("NTFY_TOPIC")
    if not topic:
        return
    req = urllib.request.Request(
        f"https://ntfy.sh/{topic}", data=msg.encode("utf-8"), method="POST",
        headers={"Title": title, "Click": "https://bilet.atelje212.rs/repertoar.php",
                 "Tags": "performing_arts"},
    )
    urllib.request.urlopen(req, timeout=15)


def main() -> int:
    try:
        shows = fetch_month(YEAR, MONTH)
    except Exception as e:  # network / JSON error
        print(f"Request failed: {e}", file=sys.stderr)
        return 2

    if not shows:
        print(f"{YEAR}-{MONTH:02d}: no shows published yet.")
        return 1

    lines = [f"{s['datum']} {s['vreme'][:5]}  {s['predstava'].strip()}" for s in shows]
    summary = f"{len(shows)} shows published for {YEAR}-{MONTH:02d}"
    print(summary)
    print("\n".join(lines))
    notify("Atelje 212: December repertoire is out!",
           summary + "\n" + "\n".join(lines[:10]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
