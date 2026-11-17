import asyncio
import redis.asyncio as aioredis

async def main():
    try:
        r = await aioredis.from_url('redis://localhost:6379/0')
        await r.ping()
        print("Redis is UP")
        await r.aclose()
    except Exception as e:
        print(f"Redis is DOWN: {type(e).__name__}")

asyncio.run(main())
