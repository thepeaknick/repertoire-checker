# repertoire-checker

Hourly check whether Atelje 212 (bilet.atelje212.rs) has published its December repertoire.

It calls the same endpoint the repertoar page uses (`POST qrydata.php`, `q=1`, `godina`, `mesec`) and counts real shows for the month. When shows appear it sends a push via [ntfy](https://ntfy.sh) and the workflow disables itself.

## Setup
1. Install the ntfy app and subscribe to a hard-to-guess topic.
2. Repo Settings → Secrets → Actions → add `NTFY_TOPIC`.
3. Actions → "Atelje 212 December watch" → Run workflow (sanity check).

Local run: `python3 check_december.py` (exit 0 = found, 1 = empty, 2 = request failed).
Override with `YEAR=2027 MONTH=1`.
