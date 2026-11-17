import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect('postgresql://olenevod:olenevod_dev@localhost:5432/olenevod_test')
    tables = await conn.fetch("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
    print('Tables:', [t['tablename'] for t in tables])
    
    # Check if users table exists and has data
    try:
        users = await conn.fetch("SELECT email, is_verified FROM users LIMIT 5")
        print('Users:', [(u['email'], u['is_verified']) for u in users])
    except Exception as e:
        print(f'Users query error: {type(e).__name__}: {e}')
    
    await conn.close()

asyncio.run(main())
