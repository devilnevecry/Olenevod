import CrudPage from "../components/CrudPage";

export default function VariantsPage() {
  return (
    <CrudPage
      title="Варианты товара"
      path="/admin/variants"
      idField="id"
      defaultForm={{
        product_id: "",
        sku: "",
        name: "",
        unit_type: "piece",
        pack_weight_g: "",
        barcode: "",
      }}
      fields={[
        { key: "product_id", label: "Товар (ID)", type: "text" },
        { key: "sku", label: "SKU", type: "text" },
        { key: "name", label: "Название", type: "text" },
        {
          key: "unit_type",
          label: "Единица измерения",
          type: "select",
          options: [
            { value: "piece", label: "Штука" },
            { value: "weight", label: "Вес" },
          ],
        },
        { key: "pack_weight_g", label: "Вес упаковки (г)", type: "number" },
        { key: "barcode", label: "Штрихкод", type: "text" },
      ]}
      toPayload={(f) => ({
        product_id: f.product_id,
        sku: f.sku,
        name: f.name,
        unit_type: f.unit_type,
        pack_weight_g: f.pack_weight_g ? Number(f.pack_weight_g) : undefined,
        barcode: f.barcode || undefined,
      })}
      itemToForm={(i) => ({
        product_id: i.product_id ?? "",
        sku: i.sku ?? "",
        name: i.name ?? "",
        unit_type: i.unit_type ?? "piece",
        pack_weight_g: i.pack_weight_g ?? "",
        barcode: i.barcode ?? "",
      })}
      columns={[
        { key: "id", label: "ID" },
        { key: "product_id", label: "Товар (ID)" },
        { key: "sku", label: "SKU" },
        { key: "name", label: "Название" },
        { key: "unit_type", label: "Единица" },
        { key: "pack_weight_g", label: "Вес (г)" },
        { key: "barcode", label: "Штрихкод" },
      ]}
    />
  );
}
