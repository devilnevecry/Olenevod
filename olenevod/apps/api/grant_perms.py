import asyncio
import asyncpg

async def main():
    try:
        c = await asyncpg.connect('postgresql://postgres:postgres@localhost:5432/olenevod_test')
        await c.execute('GRANT ALL ON users TO olenevod')
        await c.execute('GRANT ALL ON email_verification_codes TO olenevod')
        print('Permissions granted')
        await c.close()
    except Exception as e:
        print(f'Error: {type(e).__name__}: {e}')

asyncio.run(main())
