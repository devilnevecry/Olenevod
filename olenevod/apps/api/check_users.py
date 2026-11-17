import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect('postgresql://olenevod:olenevod_dev@localhost:5432/olenevod_test')
    users = await conn.fetch("SELECT email, is_verified FROM users")
    print('Users:', [(u['email'], u['is_verified']) for u in users])
    await conn.close()

asyncio.run(main())
