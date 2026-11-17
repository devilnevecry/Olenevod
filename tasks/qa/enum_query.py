import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect(user="olenevod", password="olenevod_dev", database="olenevod_test", host="localhost", port=5432)
    try:
        rows = await conn.fetch("""
            SELECT t.typname AS enum_name, e.enumlabel AS value
            FROM pg_type t
            JOIN pg_enum e ON e.enumtypid = t.oid
            WHERE t.typname = 'order_status'
            ORDER BY e.enumsortorder
        """)
        print("order_status enum values:")
        for r in rows:
            print(" -", r["value"])
        if not rows:
            print("  (no enum type order_status found)")
    finally:
        await conn.close()

asyncio.run(main())
