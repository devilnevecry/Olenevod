import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect('postgresql://olenevod:olenevod_dev@localhost:5432/olenevod_test')
    try:
        result = await conn.fetchval("SELECT count(*) FROM users")
        print(f'Users count: {result}')
    except Exception as e:
        print(f'Error: {type(e).__name__}: {e}')
    await conn.close()

asyncio.run(main())
