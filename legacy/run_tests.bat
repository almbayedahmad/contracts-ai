@echo off
setlocal
cd /d %~dp0
echo Running unit tests...
pytest -q
endlocal
