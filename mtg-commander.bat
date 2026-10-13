@echo off
REM Windows entry point for mtg-commander, the Commander deck builder; forwards all args.
REM Usage: mtg-commander.bat upgrade --precon "Squirreled Away" --budget 75
python "%~dp0src\mtg-commander.py" %*
