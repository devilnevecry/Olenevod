import asyncio
import redis.asyncio as aioredis

async def main():
    r = await aioredis.from_url('redis://localhost:6379/0', decode_responses=True)
    keys = await r.keys('rate_limit:login:*')
    print('Keys before:', keys)
    if keys:
        await r.delete(*keys)
    keys2 = await r.keys('rate_limit:login:*')
    print('Keys after:', keys2)
    await r.aclose()

asyncio.run(main())
