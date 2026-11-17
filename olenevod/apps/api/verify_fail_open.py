import asyncio
import httpx

BASE = "http://127.0.0.1:8000"
EMAIL = "ivan@example.com"
WRONG_PASSWORD = "wrongpassword123"
CORRECT_PASSWORD = "DemoPass123"

async def main():
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Wrong password without Redis - should get 401 (fail-open allows request)
        r = await client.post(f"{BASE}/auth/login", json={
            "email": EMAIL,
            "password": WRONG_PASSWORD,
        })
        print(f"Fail-open wrong password: {r.status_code} {r.text.encode('ascii', 'replace').decode()}")

        # Correct password without Redis - should get 200 (fail-open allows request)
        r = await client.post(f"{BASE}/auth/login", json={
            "email": EMAIL,
            "password": CORRECT_PASSWORD,
        })
        print(f"Fail-open correct password: {r.status_code} {r.text.encode('ascii', 'replace').decode()}")

asyncio.run(main())
