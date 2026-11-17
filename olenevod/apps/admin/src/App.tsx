import { Navigate, createBrowserRouter, RouterProvider } from "react-router-dom";
import { Layout } from "./components/Layout";
import Login from "./pages/login";
import CitiesPage from "./pages/cities";
import WarehousesPage from "./pages/warehouses";
import ProductsPage from "./pages/products";
import VariantsPage from "./pages/variants";
import OffersPage from "./pages/offers";
import StockPage from "./pages/stock";
import TransfersPage from "./pages/transfers";
import RoutesPage from "./pages/routes";
import CarriersPage from "./pages/carriers";
import OrdersPage from "./pages/orders";
import CustomersPage from "./pages/customers";

function PrivateRoute({ element }: { element: React.ReactNode }) {
  const token = localStorage.getItem("admin_token");
  if (!token) return <Navigate to="/login" replace />;
  return <Layout>{element}</Layout>;
}

const router = createBrowserRouter([
  { path: "/login", element: <Login /> },
  { path: "/", element: <Navigate to="/cities" replace /> },
  { path: "/cities", element: <PrivateRoute element={<CitiesPage />} /> },
  { path: "/warehouses", element: <PrivateRoute element={<WarehousesPage />} /> },
  { path: "/products", element: <PrivateRoute element={<ProductsPage />} /> },
  { path: "/variants", element: <PrivateRoute element={<VariantsPage />} /> },
  { path: "/offers", element: <PrivateRoute element={<OffersPage />} /> },
  { path: "/stock", element: <PrivateRoute element={<StockPage />} /> },
  { path: "/transfers", element: <PrivateRoute element={<TransfersPage />} /> },
  { path: "/routes", element: <PrivateRoute element={<RoutesPage />} /> },
  { path: "/carriers", element: <PrivateRoute element={<CarriersPage />} /> },
  { path: "/orders", element: <PrivateRoute element={<OrdersPage />} /> },
  { path: "/customers", element: <PrivateRoute element={<CustomersPage />} /> },
]);

export default function App() {
  return <RouterProvider router={router} />;
}
