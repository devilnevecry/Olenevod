import asyncio
import httpx

BASE = "http://127.0.0.1:8000"
EMAIL = "ivan@example.com"
WRONG_PASSWORD = "wrongpassword123"
CORRECT_PASSWORD = "DemoPass123"

async def main():
    async with httpx.AsyncClient() as client:
        # Clear Redis counters first
        import redis.asyncio as aioredis
        r = await aioredis.from_url('redis://localhost:6379/0', decode_responses=True)
        keys = await r.keys('rate_limit:login:*')
        if keys:
            await r.delete(*keys)
        print(f"Redis keys cleared: {len(keys)} keys deleted")
        await r.aclose()

        # 5 failed login attempts (expect 401 each)
        for i in range(1, 6):
            resp = await client.post(f"{BASE}/auth/login", json={
                "email": EMAIL,
                "password": WRONG_PASSWORD,
            })
            print(f"Failed attempt {i}: {resp.status_code} {resp.text.encode('ascii', 'replace').decode()}")

        # 6th failed attempt (expect 429)
        resp = await client.post(f"{BASE}/auth/login", json={
            "email": EMAIL,
            "password": WRONG_PASSWORD,
        })
        print(f"6th attempt (expect 429): {resp.status_code} {resp.text.encode('ascii', 'replace').decode()}")

        # Successful login (expect 200, counter resets)
        resp = await client.post(f"{BASE}/auth/login", json={
            "email": EMAIL,
            "password": CORRECT_PASSWORD,
        })
        print(f"Successful login: {resp.status_code} {resp.text.encode('ascii', 'replace').decode()}")

        # After success, failed attempts should work again (counter reset)
        resp = await client.post(f"{BASE}/auth/login", json={
            "email": EMAIL,
            "password": WRONG_PASSWORD,
        })
        print(f"Attempt after success (expect 401): {resp.status_code} {resp.text.encode('ascii', 'replace').decode()}")

asyncio.run(main())
