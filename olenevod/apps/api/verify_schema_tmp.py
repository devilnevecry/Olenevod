import asyncio, asyncpg

async def main():
    conn = await asyncpg.connect('postgresql://postgres:postgres@localhost:5432/olenevod_test')
    col = await conn.fetchval("SELECT column_name FROM information_schema.columns WHERE table_name='orders' AND column_name='idempotency_key'")
    print('Column idempotency_key:', col)
    cons = await conn.fetchval("SELECT constraint_name FROM information_schema.table_constraints WHERE table_name='orders' AND constraint_name='uq_orders_idempotency_key'")
    print('Unique constraint:', cons)
    idx = await conn.fetchval("SELECT indexname FROM pg_indexes WHERE tablename='orders' AND indexname='ix_orders_idempotency_key'")
    print('Index:', idx)
    await conn.close()

asyncio.run(main())
