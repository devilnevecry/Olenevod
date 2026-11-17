@echo off
set SECRET_KEY=dev-secret-key-do-not-use-in-production
"C:\Users\nu11\Documents\GitHub\kilo-hub\data\worktrees\mwkfedqhnoov\1.T43\.venv\Scripts\python.exe" -m uvicorn olenevod.interfaces.http.app:app --host 127.0.0.1 --port 8001
