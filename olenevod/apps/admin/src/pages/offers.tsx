import CrudPage from "../components/CrudPage";

export default function OffersPage() {
  return (
    <CrudPage
      title="Предложения города"
      path="/admin/offers"
      idField="id"
      defaultForm={{
        city_id: "",
        variant_id: "",
        price_kop: "",
        old_price_kop: "",
        is_published: true,
        min_qty: "1",
        step_qty: "1",
        max_qty_per_order: "",
      }}
      fields={[
        { key: "city_id", label: "Город (ID)", type: "text" },
        { key: "variant_id", label: "Вариант (ID)", type: "text" },
        { key: "price_kop", label: "Цена (коп)", type: "number" },
        { key: "old_price_kop", label: "Старая цена (коп)", type: "number" },
        { key: "is_published", label: "Опубликован", type: "boolean" },
        { key: "min_qty", label: "Мин. qty", type: "number" },
        { key: "step_qty", label: "Шаг qty", type: "number" },
        { key: "max_qty_per_order", label: "Макс. qty в заказе", type: "number" },
      ]}
      toPayload={(f) => ({
        city_id: f.city_id,
        variant_id: f.variant_id,
        price_kop: f.price_kop ? Number(f.price_kop) : undefined,
        old_price_kop: f.old_price_kop ? Number(f.old_price_kop) : undefined,
        is_published: f.is_published === true || f.is_published === "true",
        min_qty: f.min_qty ? Number(f.min_qty) : undefined,
        step_qty: f.step_qty ? Number(f.step_qty) : undefined,
        max_qty_per_order: f.max_qty_per_order ? Number(f.max_qty_per_order) : undefined,
      })}
      itemToForm={(i) => ({
        city_id: i.city_id ?? "",
        variant_id: i.variant_id ?? "",
        price_kop: i.price_kop ?? "",
        old_price_kop: i.old_price_kop ?? "",
        is_published: !!i.is_published,
        min_qty: i.min_qty ?? "",
        step_qty: i.step_qty ?? "",
        max_qty_per_order: i.max_qty_per_order ?? "",
      })}
      columns={[
        { key: "id", label: "ID" },
        { key: "city_id", label: "Город (ID)" },
        { key: "variant_id", label: "Вариант (ID)" },
        { key: "price_kop", label: "Цена (коп)" },
        { key: "is_published", label: "Опубликован", render: (i) => (i.is_published ? "Да" : "Нет") },
        { key: "min_qty", label: "Мин. qty" },
        { key: "step_qty", label: "Шаг qty" },
      ]}
    />
  );
}
