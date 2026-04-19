import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { apiFetch, setAuthToken } from "@/lib/api";

export type UserRole = "super_admin" | "data_entry" | "inventory";

// Backend shape (snake_case from Postgres)
export interface ApiUser {
  id: string;
  username: string;
  full_name: string;
  role: UserRole;
  active: boolean;
  created_at: string;
}

// Frontend shape (camelCase used across the app)
export interface AppUser {
  id: string;
  username: string;
  fullName: string;
  role: UserRole;
  active: boolean;
  createdAt: string;
}

const SESSION_KEY = "pvd_session";

export function fromApi(u: ApiUser): AppUser {
  return {
    id: u.id,
    username: u.username,
    fullName: u.full_name,
    role: u.role,
    active: u.active,
    createdAt: u.created_at,
  };
}

// Hook: load users from backend
export function useUsers() {
  const [users, setUsers] = useState<AppUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const list = await apiFetch<ApiUser[]>("/api/users");
      setUsers(list.map(fromApi));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load users");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const handler = () => refresh();
    window.addEventListener("pvd_users_changed", handler);
    return () => window.removeEventListener("pvd_users_changed", handler);
  }, [refresh]);

  return { users, loading, error, refresh };
}

export function notifyUsersChanged() {
  window.dispatchEvent(new Event("pvd_users_changed"));
}

// User CRUD helpers (call backend)
export async function createUser(input: { username: string; password: string; fullName: string; role: UserRole; active: boolean }): Promise<AppUser> {
  const created = await apiFetch<ApiUser>("/api/users", {
    method: "POST",
    body: JSON.stringify({
      username: input.username,
      password: input.password,
      full_name: input.fullName,
      role: input.role,
      active: input.active,
    }),
  });
  notifyUsersChanged();
  return fromApi(created);
}

export async function updateUser(id: string, input: { username: string; password?: string; fullName: string; role: UserRole; active: boolean }): Promise<AppUser> {
  const updated = await apiFetch<ApiUser>(`/api/users/${id}`, {
    method: "PUT",
    body: JSON.stringify({
      username: input.username,
      password: input.password || undefined,
      full_name: input.fullName,
      role: input.role,
      active: input.active,
    }),
  });
  notifyUsersChanged();
  return fromApi(updated);
}

export async function setUserActive(user: AppUser, active: boolean): Promise<AppUser> {
  return updateUser(user.id, {
    username: user.username,
    fullName: user.fullName,
    role: user.role,
    active,
  });
}

export async function deleteUser(id: string): Promise<void> {
  await apiFetch(`/api/users/${id}`, { method: "DELETE" });
  notifyUsersChanged();
}

// Role permissions
const ROLE_ROUTES: Record<UserRole, string[]> = {
  super_admin: ["/", "/data-entry", "/settings", "/users"],
  data_entry: ["/", "/data-entry"],
  inventory: ["/"],
};

export function canAccessRoute(role: UserRole, path: string): boolean {
  return ROLE_ROUTES[role]?.includes(path) ?? false;
}

export function getRoleLabel(role: UserRole): string {
  switch (role) {
    case "super_admin": return "Super Admin";
    case "data_entry": return "Data Entry";
    case "inventory": return "Inventory";
  }
}

// Auth context — login hits the backend
interface AuthContextValue {
  user: AppUser | null;
  login: (username: string, password: string) => Promise<string | null>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AppUser | null>(() => {
    try {
      const raw = localStorage.getItem(SESSION_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  });

  const login = useCallback(async (username: string, password: string): Promise<string | null> => {
    try {
      const resp = await apiFetch<ApiUser & { token: string }>("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ username, password }),
      });
      const { token, ...apiUser } = resp;
      setAuthToken(token);
      const u = fromApi(apiUser);
      localStorage.setItem(SESSION_KEY, JSON.stringify(u));
      setUser(u);
      return null;
    } catch (e) {
      return e instanceof Error ? e.message : "Login failed";
    }
  }, []);

  const logout = useCallback(() => {
    setAuthToken(null);
    localStorage.removeItem(SESSION_KEY);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
