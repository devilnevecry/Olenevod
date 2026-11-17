import { Client } from "pg"

const DB_CONFIG = {
  host: "localhost",
  port: 5432,
  user: "postgres",
  password: "postgres",
  database: "olenevod_test",
} as const

// Идемпотентный сид seed-данных для E2E тестов витрины (этапы 12 и 13):
// города, категории, товары, варианты, остатки, зоны и тарифы доставки.
// Безопасно запускать повторно (все вставки — ON CONFLICT).
const SEED_SQL = `
INSERT INTO cities (id, slug, name, region, timezone, is_active) VALUES
  ('11111111-1111-1111-1111-111111111001', 'moscow', 'Москва', 'Москва', 'Europe/Moscow', true),
  ('11111111-1111-1111-1111-111111111002', 'spb', 'Санкт-Петербург', 'Санкт-Петербург', 'Europe/Moscow', true)
ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO categories (id, parent_id, slug, name, is_published, sort) VALUES
  ('22222222-2222-2222-2222-222222222001', NULL, 'produkty', 'Продукты', true, 10),
  ('22222222-2222-2222-2222-222222222002', '22222222-2222-2222-2222-222222222001', 'moloko', 'Молоко и молочные продукты', true, 20),
  ('22222222-2222-2222-2222-222222222003', NULL, 'zakazy-test', 'Тест заказов', true, 100)
ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO products (id, category_id, slug, name, short_description, is_published) VALUES
  ('33333333-3333-3333-3333-333333333001', '22222222-2222-2222-2222-222222222002', 'moloko-klassicheskoe', 'Молоко классическое', 'Пастеризованное 2,5%', true),
  ('33333333-3333-3333-3333-333333333002', '22222222-2222-2222-2222-222222222003', 'zakaz-produkt', 'Продукт для заказа', null, true)
ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO product_variants (id, product_id, sku, name, unit_type, pack_weight_g) VALUES
  ('44444444-4444-4444-4444-444444444001', '33333333-3333-3333-3333-333333333001', 'MOLOKO-1L', '1 л', 'piece', 1000),
  ('44444444-4444-4444-4444-444444444002', '33333333-3333-3333-3333-333333333002', 'ZAKAZ-001', 'Вариант для заказа', 'piece', 800)
ON CONFLICT (sku) DO UPDATE SET name = EXCLUDED.name, pack_weight_g = EXCLUDED.pack_weight_g;

INSERT INTO city_offers (id, city_id, variant_id, price_kop, old_price_kop, is_published) VALUES
  ('66666666-6666-6666-6666-666666666001', '11111111-1111-1111-1111-111111111001', '44444444-4444-4444-4444-444444444001', 9500, 10500, true),
  ('66666666-6666-6666-6666-666666666002', '11111111-1111-1111-1111-111111111002', '44444444-4444-4444-4444-444444444001', 9900, NULL, true),
  ('66666666-6666-6666-6666-666666666003', '11111111-1111-1111-1111-111111111001', '44444444-4444-4444-4444-444444444002', 9500, NULL, true)
ON CONFLICT (city_id, variant_id) DO UPDATE SET price_kop = EXCLUDED.price_kop;

INSERT INTO warehouses (id, city_id, name, address, is_active) VALUES
  ('55555555-5555-5555-5555-555555555001', '11111111-1111-1111-1111-111111111001', 'Склад Москва-1', 'ул. Тестовая, 1', true),
  ('55555555-5555-5555-5555-555555555002', '11111111-1111-1111-1111-111111111001', 'Склад Москва-2', 'ул. Тестовая, 2', true),
  ('55555555-5555-5555-5555-555555555003', '11111111-1111-1111-1111-111111111001', 'Склад заказы', null, true)
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO stock_levels (warehouse_id, variant_id, on_hand, reserved) VALUES
  ('55555555-5555-5555-5555-555555555001', '44444444-4444-4444-4444-444444444001', 10, 2),
  ('55555555-5555-5555-5555-555555555002', '44444444-4444-4444-4444-444444444001', 5, 0),
  ('55555555-5555-5555-5555-555555555003', '44444444-4444-4444-4444-444444444002', 100, 0)
ON CONFLICT (warehouse_id, variant_id) DO UPDATE SET on_hand = EXCLUDED.on_hand, reserved = EXCLUDED.reserved;

INSERT INTO delivery_zones (id, city_id, zone_name, base_fee, per_kg_fee, free_from_amount) VALUES
  ('77777777-7777-7777-7777-777777777003', '11111111-1111-1111-1111-111111111001', 'Москва внутри МКАД', 500, 100, 20000)
ON CONFLICT (city_id) DO UPDATE SET zone_name = EXCLUDED.zone_name;

INSERT INTO delivery_tariffs (id, zone_id, name, estimated_days, is_active) VALUES
  ('88888888-8888-8888-8888-888888888003', '77777777-7777-7777-7777-777777777003', 'Курьер Москва', 3, true)
ON CONFLICT (zone_id) DO UPDATE SET name = EXCLUDED.name;
`

export async function seedCatalog(): Promise<void> {
  const client = new Client(DB_CONFIG)
  await client.connect()
  try {
    const statements = SEED_SQL.split(";").map((statement) => statement.trim()).filter(Boolean)
    for (const statement of statements) {
      await client.query(statement)
    }
  } finally {
    await client.end()
  }
}
