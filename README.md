# repertoire-checker

Checks every 10 minutes whether Atelje 212 (bilet.atelje212.rs) has published its December repertoire.

It calls the same endpoint the repertoar page uses (`POST qrydata.php`, `q=1`, `godina`, `mesec`) and counts real shows for the month.

- **Shows found** → urgent push via [ntfy](https://ntfy.sh), then the workflow disables itself.
- **Check broken** (site down, response format changed) → warning push, at most once an hour, and the run goes red.

## Setup
1. Install the ntfy app and subscribe to your topic.
2. Repo Settings → Secrets → Actions → add `NTFY_TOPIC`.
3. Actions → "Atelje 212 December watch" → Run workflow (sanity check).

Local run: `python3 check_december.py` (exit 0 = found, 1 = empty, 2 = check broken).
Override with `YEAR=2027 MONTH=1`.

## Second watcher on the Mac (launchd, every 15 min)
```bash
sed 's/YOUR_NTFY_TOPIC/<your-topic>/' launchd/rs.atelje212.repertoire-checker.plist \
  > ~/Library/LaunchAgents/rs.atelje212.repertoire-checker.plist
launchctl load ~/Library/LaunchAgents/rs.atelje212.repertoire-checker.plist
tail -f /tmp/repertoire-checker.log      # check it's running
```
Once shows are found it writes `.found` and stays quiet. To remove:
```bash
launchctl unload ~/Library/LaunchAgents/rs.atelje212.repertoire-checker.plist
rm ~/Library/LaunchAgents/rs.atelje212.repertoire-checker.plist
```
