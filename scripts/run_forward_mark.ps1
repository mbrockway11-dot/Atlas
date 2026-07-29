# One frequent mark-to-market tick: refresh live prices and revalue the held
# book, logging an equity point. Does NOT rebalance (signals only change daily,
# so intraday re-trading would only churn fees). Meant to run every 1-5 minutes;
# the daily task handles the actual rebalance. Paper-only.
$ErrorActionPreference = "Continue"
$py = ".\.venv\Scripts\python.exe"
& $py scripts/quick_snapshot.py | Out-Null
& $py scripts/run_forward_paper.py --mark-only
