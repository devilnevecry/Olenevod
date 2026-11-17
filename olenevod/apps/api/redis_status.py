import asyncio
import redis.asyncio as aioredis

async def main():
    # Start Redis is not possible from Python, but we can check if it's running
    # and try to reconnect
    try:
        r = await aioredis.from_url('redis://localhost:6379/0', decode_responses=True)
        await r.ping()
        print("Redis is already UP")
        await r.aclose()
    except Exception as e:
        print(f"Redis is DOWN: {type(e).__name__}: {e}")

asyncio.run(main())
