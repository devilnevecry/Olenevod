import CrudPage from "../components/CrudPage";

export default function ProductsPage() {
  return (
    <CrudPage
      title="Товары"
      path="/admin/products"
      idField="id"
      defaultForm={{
        category_id: "",
        slug: "",
        name: "",
        short_description: "",
        description: "",
        is_published: true,
        is_demo: false,
      }}
      fields={[
        { key: "category_id", label: "Категория (ID)", type: "text" },
        { key: "slug", label: "Slug", type: "text" },
        { key: "name", label: "Название", type: "text" },
        { key: "short_description", label: "Короткое описание", type: "text" },
        { key: "description", label: "Описание", type: "text" },
        { key: "is_published", label: "Опубликован", type: "boolean" },
        { key: "is_demo", label: "Демо", type: "boolean" },
      ]}
      toPayload={(f) => ({
        category_id: f.category_id,
        slug: f.slug,
        name: f.name,
        short_description: f.short_description || undefined,
        description: f.description || undefined,
        is_published: f.is_published === true || f.is_published === "true",
        is_demo: f.is_demo === true || f.is_demo === "true",
      })}
      itemToForm={(i) => ({
        category_id: i.category_id ?? "",
        slug: i.slug ?? "",
        name: i.name ?? "",
        short_description: i.short_description ?? "",
        description: i.description ?? "",
        is_published: !!i.is_published,
        is_demo: !!i.is_demo,
      })}
      columns={[
        { key: "id", label: "ID" },
        { key: "category_id", label: "Категория (ID)" },
        { key: "slug", label: "Slug" },
        { key: "name", label: "Название" },
        { key: "is_published", label: "Опубликован", render: (i) => (i.is_published ? "Да" : "Нет") },
        { key: "is_demo", label: "Демо", render: (i) => (i.is_demo ? "Да" : "Нет") },
      ]}
    />
  );
}
