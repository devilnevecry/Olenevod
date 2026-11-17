import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect(
        user="olenevod", password="olenevod_dev",
        database="olenevod_test", host="localhost", port=5432,
    )
    try:
        out = open("tasks\\qa\\seed_out.txt", "w", encoding="utf-8")
        async def q(label, sql):
            out.write(f"\n=== {label} ===\n")
            rows = await conn.fetch(sql)
            for r in rows:
                out.write(str(tuple(r)) + "\n")
            out.flush()
        await q("users", "SELECT id, email, name, is_verified FROM users ORDER BY created_at LIMIT 20")
        await q("cities", "SELECT id, slug, name, region, is_active FROM cities ORDER BY name")
        await q("warehouses", "SELECT id, city_id, name, address, is_active FROM warehouses ORDER BY name")
        await q("products", "SELECT id, slug, name, is_published, is_demo FROM products ORDER BY name LIMIT 30")
        await q("variants", "SELECT id, product_id, sku, name, pack_weight_g FROM product_variants ORDER BY name LIMIT 40")
        await q("city_offers", "SELECT id, city_id, variant_id, price_kop, old_price_kop, is_published FROM city_offers ORDER BY id LIMIT 40")
        await q("stock_levels", "SELECT warehouse_id, variant_id, on_hand, reserved FROM stock_levels ORDER BY warehouse_id, variant_id LIMIT 60")
        await q("delivery_zones", "SELECT id, city_id, zone_name, base_fee, per_kg_fee, free_from_amount FROM delivery_zones ORDER BY city_id")
        await q("delivery_tariffs", "SELECT id, zone_id, name, estimated_days, is_active FROM delivery_tariffs ORDER BY id")
        out.write("\nDONE\n")
        out.close()
    finally:
        await conn.close()

asyncio.run(main())
