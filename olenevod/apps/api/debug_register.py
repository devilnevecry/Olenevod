import asyncio
import httpx

BASE = "http://127.0.0.1:8000"

async def main():
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{BASE}/auth/register", json={
            "email": "debug-test@example.com",
            "name": "Debug Test",
            "password": "testpass123",
        })
        print(f"Status: {r.status_code}")
        print(f"Body: {r.text}")
        print(f"Headers: {dict(r.headers)}")

asyncio.run(main())
