@echo off
echo Starting Virtual Try-On Server with extended timeouts...
cd /d %~dp0
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --timeout-keep-alive 600 --limit-concurrency 1 --workers 1