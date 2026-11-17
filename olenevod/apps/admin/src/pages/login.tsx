import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login, setToken } from "../api";
import { Button } from "../components/Button";
import { Input } from "../components/Input";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await login(email, password);
      setToken(data.access_token);
      navigate("/cities", { replace: true });
    } catch (err: any) {
      setError(err.message || "Неверный e-mail или пароль");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "100vh",
        background: "#f8fafc",
      }}
    >
      <div
        style={{
          background: "#fff",
          padding: 32,
          borderRadius: 8,
          boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
          width: 360,
        }}
      >
        <h2 style={{ margin: 0, fontSize: 20, fontWeight: 700, marginBottom: 20 }}>Вход в админ-панель</h2>
        {error && (
          <div
            style={{
              color: "#b91c1c",
              background: "#fee2e2",
              padding: 8,
              borderRadius: 6,
              marginBottom: 16,
              fontSize: 14,
            }}
          >
            {error}
          </div>
        )}
        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <Input label="E-mail" value={email} onChange={(e) => setEmail(e.target.value)} type="email" />
          <Input label="Пароль" value={password} onChange={(e) => setPassword(e.target.value)} type="password" />
          <Button type="submit" variant="primary" disabled={loading} style={{ width: "100%" }}>
            {loading ? "Вход..." : "Войти"}
          </Button>
        </form>
      </div>
    </div>
  );
}
