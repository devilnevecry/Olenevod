import asyncio
import redis.asyncio as aioredis

async def main():
    # Shutdown Redis
    try:
        r = await aioredis.from_url('redis://localhost:6379/0', decode_responses=True)
        await r.shutdown()
        await r.aclose()
        print("Redis shutdown")
    except Exception as e:
        print(f"Redis shutdown error: {type(e).__name__}: {e}")

asyncio.run(main())
