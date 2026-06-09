@echo off
REM Windows entry point for mtg-draft — forwards all args to the Python CLI.
REM Usage: mtg-draft.bat warm --set FIN   /   mtg-draft.bat pull   etc.
python "%~dp0src\mtg-draft.py" %*
