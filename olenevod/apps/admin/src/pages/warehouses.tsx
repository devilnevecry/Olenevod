import CrudPage from "../components/CrudPage";

export default function WarehousesPage() {
  return (
    <CrudPage
      title="Склады"
      path="/admin/warehouses"
      idField="id"
      defaultForm={{ city_id: "", name: "", address: "", is_active: true }}
      fields={[
        { key: "city_id", label: "Город (ID)", type: "text" },
        { key: "name", label: "Название", type: "text" },
        { key: "address", label: "Адрес", type: "text" },
        { key: "is_active", label: "Активен", type: "boolean" },
      ]}
      toPayload={(f) => ({
        city_id: f.city_id,
        name: f.name,
        address: f.address || undefined,
        is_active: f.is_active === true || f.is_active === "true",
      })}
      itemToForm={(i) => ({
        city_id: i.city_id ?? "",
        name: i.name ?? "",
        address: i.address ?? "",
        is_active: !!i.is_active,
      })}
      columns={[
        { key: "id", label: "ID" },
        { key: "city_id", label: "Город (ID)" },
        { key: "name", label: "Название" },
        { key: "address", label: "Адрес" },
        { key: "is_active", label: "Активен", render: (i) => (i.is_active ? "Да" : "Нет") },
      ]}
    />
  );
}
