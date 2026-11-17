/// <reference types="vite/client" />
const API_BASE = (import.meta.env.VITE_API_URL as string | undefined) ?? "http://localhost:8000";
const TOKEN_KEY = "admin_token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string | null) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

function headers(extra: Record<string, string> = {}): Record<string, string> {
  const token = getToken();
  const h: Record<string, string> = { "Content-Type": "application/json", ...extra };
  if (token) h["Authorization"] = `Bearer ${token}`;
  return h;
}

async function handleResponse(res: Response): Promise<any> {
  if (res.status === 204) return undefined;
  const text = await res.text();
  if (!res.ok) throw new Error(`${res.status} ${text}`);
  if (!text) return undefined;
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

export async function api(path: string, opts: RequestInit = {}): Promise<any> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...opts,
    headers: { ...headers(), ...(opts.headers as Record<string, string> | undefined) },
  });
  return handleResponse(res);
}

export function get<T>(path: string, params: Record<string, string> = {}): Promise<T> {
  const qs = new URLSearchParams(params).toString();
  const url = qs ? `${path}?${qs}` : path;
  return api(url, { method: "GET" });
}

export function del(path: string): Promise<any> {
  return api(path, { method: "DELETE" });
}

export function post<T>(path: string, body: any): Promise<T> {
  return api(path, { method: "POST", body: JSON.stringify(body) });
}

export function patch<T>(path: string, body: any): Promise<T> {
  return api(path, { method: "PATCH", body: JSON.stringify(body) });
}

export async function login(email: string, password: string): Promise<{ access_token: string; user_id: string }> {
  return api("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}
