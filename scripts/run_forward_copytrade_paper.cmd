@echo off
REM Wrapper for the daily forward-paper copy-trade cycle (Windows Task Scheduler).
REM Sets the working directory so the script's relative output/ and registry paths
REM resolve, uses the project venv interpreter, and appends a run log. Read-only
REM market data, paper-only -- no signing path.
cd /d C:\Projects\Atlas
set PYTHONIOENCODING=utf-8
if not exist output\investment_forward_copytrade mkdir output\investment_forward_copytrade
echo ==== %DATE% %TIME% ==== >> output\investment_forward_copytrade\cron.log
.venv\Scripts\python.exe scripts\run_forward_copytrade_paper.py --ab %* >> output\investment_forward_copytrade\cron.log 2>&1
