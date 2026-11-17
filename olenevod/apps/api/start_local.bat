@echo off
set SECRET_KEY=dev-secret-key-do-not-use-in-production
..\..\.venv\Scripts\python.exe -m uvicorn olenevod.interfaces.http.app:app --host 127.0.0.1 --port 8001
