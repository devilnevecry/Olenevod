-- Сид заказов для E2E этапа 13 (реальная БД olenevod_test).
-- Все вставки идемпотентны (ON CONFLICT), безопасно повторять перед каждым прогоном.
INSERT INTO cities (id, slug, name, region, timezone, is_active) VALUES
  ('11111111-1111-1111-1111-111111111001', 'moscow', 'Москва', 'Москва', 'Europe/Moscow', true)
ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO categories (id, parent_id, slug, name, is_published, sort) VALUES
  ('22222222-2222-2222-2222-222222222003', NULL, 'zakazy-test', 'Тест заказов', true, 100)
ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO products (id, category_id, slug, name, is_published) VALUES
  ('33333333-3333-3333-3333-333333333002', '22222222-2222-2222-2222-222222222003', 'zakaz-produkt', 'Продукт для заказа', true)
ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO product_variants (id, product_id, sku, name, unit_type, pack_weight_g) VALUES
  ('44444444-4444-4444-4444-444444444002', '33333333-3333-3333-3333-333333333002', 'ZAKAZ-001', 'Вариант для заказа', 'piece', 800)
ON CONFLICT (sku) DO UPDATE SET pack_weight_g = EXCLUDED.pack_weight_g;

INSERT INTO city_offers (id, city_id, variant_id, price_kop, is_published) VALUES
  ('66666666-6666-6666-6666-666666666003', '11111111-1111-1111-1111-111111111001', '44444444-4444-4444-4444-444444444002', 9500, true)
ON CONFLICT (city_id, variant_id) DO UPDATE SET price_kop = EXCLUDED.price_kop;

INSERT INTO warehouses (id, city_id, name, is_active) VALUES
  ('55555555-5555-5555-5555-555555555003', '11111111-1111-1111-1111-111111111001', 'Склад заказы', true)
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO stock_levels (warehouse_id, variant_id, on_hand, reserved) VALUES
  ('55555555-5555-5555-5555-555555555003', '44444444-4444-4444-4444-444444444002', 100, 0)
ON CONFLICT (warehouse_id, variant_id) DO UPDATE SET on_hand = EXCLUDED.on_hand, reserved = EXCLUDED.reserved;

-- Доставка для Москвы: зона + тариф (не бесплатная при сумме корзины 9500 коп).
INSERT INTO delivery_zones (id, city_id, zone_name, base_fee, per_kg_fee, free_from_amount) VALUES
  ('77777777-7777-7777-7777-777777777003', '11111111-1111-1111-1111-111111111001', 'Москва внутри МКАД', 500, 100, 20000)
ON CONFLICT (city_id) DO UPDATE SET zone_name = EXCLUDED.zone_name;

INSERT INTO delivery_tariffs (id, zone_id, name, estimated_days, is_active) VALUES
  ('88888888-8888-8888-8888-888888888003', '77777777-7777-7777-7777-777777777003', 'Курьер Москва', 3, true)
ON CONFLICT (zone_id) DO UPDATE SET name = EXCLUDED.name;
