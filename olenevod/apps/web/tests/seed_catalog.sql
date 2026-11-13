-- Сид каталога для E2E этапа 12 (идентичен olenevod/apps/api/tests/test_catalog_routes.py).
INSERT INTO cities (id, slug, name, region, timezone, is_active) VALUES
  ('11111111-1111-1111-1111-111111111001', 'moscow', 'Москва', 'Москва', 'Europe/Moscow', true),
  ('11111111-1111-1111-1111-111111111002', 'spb', 'Санкт-Петербург', 'Санкт-Петербург', 'Europe/Moscow', true)
ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO categories (id, parent_id, slug, name, is_published, sort) VALUES
  ('22222222-2222-2222-2222-222222222001', NULL, 'produkty', 'Продукты', true, 10),
  ('22222222-2222-2222-2222-222222222002', '22222222-2222-2222-2222-222222222001', 'moloko', 'Молоко и молочные продукты', true, 20)
ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO products (id, category_id, slug, name, short_description, is_published) VALUES
  ('33333333-3333-3333-3333-333333333001', '22222222-2222-2222-2222-222222222002', 'moloko-klassicheskoe', 'Молоко классическое', 'Пастеризованное 2,5%', true)
ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO product_variants (id, product_id, sku, name, unit_type, pack_weight_g) VALUES
  ('44444444-4444-4444-4444-444444444001', '33333333-3333-3333-3333-333333333001', 'MOLOKO-1L', '1 л', 'piece', 1000)
ON CONFLICT (sku) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO city_offers (id, city_id, variant_id, price_kop, old_price_kop, is_published) VALUES
  ('66666666-6666-6666-6666-666666666001', '11111111-1111-1111-1111-111111111001', '44444444-4444-4444-4444-444444444001', 9500, 10500, true),
  ('66666666-6666-6666-6666-666666666002', '11111111-1111-1111-1111-111111111002', '44444444-4444-4444-4444-444444444001', 9900, NULL, true)
ON CONFLICT (city_id, variant_id) DO UPDATE SET price_kop = EXCLUDED.price_kop;

INSERT INTO warehouses (id, city_id, name, address, is_active) VALUES
  ('55555555-5555-5555-5555-555555555001', '11111111-1111-1111-1111-111111111001', 'Склад Москва-1', 'ул. Тестовая, 1', true),
  ('55555555-5555-5555-5555-555555555002', '11111111-1111-1111-1111-111111111001', 'Склад Москва-2', 'ул. Тестовая, 2', true)
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO stock_levels (warehouse_id, variant_id, on_hand, reserved) VALUES
  ('55555555-5555-5555-5555-555555555001', '44444444-4444-4444-4444-444444444001', 10, 2),
  ('55555555-5555-5555-5555-555555555002', '44444444-4444-4444-4444-444444444001', 5, 0)
ON CONFLICT (warehouse_id, variant_id) DO UPDATE SET on_hand = EXCLUDED.on_hand, reserved = EXCLUDED.reserved;
