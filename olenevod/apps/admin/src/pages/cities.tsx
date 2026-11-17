import CrudPage from "../components/CrudPage";

export default function CitiesPage() {
  return (
    <CrudPage
      title="Города"
      path="/admin/cities"
      idField="id"
      defaultForm={{ slug: "", name: "", region: "", timezone: "", is_active: true }}
      fields={[
        { key: "slug", label: "Slug", type: "text" },
        { key: "name", label: "Название", type: "text" },
        { key: "region", label: "Регион", type: "text" },
        { key: "timezone", label: "Часовой пояс", type: "text" },
        { key: "is_active", label: "Активен", type: "boolean" },
      ]}
      toPayload={(f) => ({
        slug: f.slug,
        name: f.name,
        region: f.region || undefined,
        timezone: f.timezone || undefined,
        is_active: f.is_active === true || f.is_active === "true",
      })}
      itemToForm={(i) => ({
        slug: i.slug ?? "",
        name: i.name ?? "",
        region: i.region ?? "",
        timezone: i.timezone ?? "",
        is_active: !!i.is_active,
      })}
      columns={[
        { key: "id", label: "ID" },
        { key: "slug", label: "Slug" },
        { key: "name", label: "Название" },
        { key: "region", label: "Регион" },
        { key: "timezone", label: "Часовой пояс" },
        { key: "is_active", label: "Активен", render: (i) => (i.is_active ? "Да" : "Нет") },
      ]}
    />
  );
}
