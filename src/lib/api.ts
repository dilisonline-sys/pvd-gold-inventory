// Base URL for the backend API.
// In Docker, the API is exposed at http://localhost:4000
// You can override at build time via VITE_API_URL.
export const API_URL =
  (import.meta.env.VITE_API_URL as string | undefined) || "http://localhost:4000";

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }));
    throw new Error(err.error || `Request failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}
