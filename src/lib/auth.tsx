import React, { createContext, useContext, useState, useEffect, useCallback } from "react";

export type UserRole = "super_admin" | "data_entry" | "inventory";

export interface AppUser {
  id: string;
  username: string;
  password: string;
  fullName: string;
  role: UserRole;
  active: boolean;
  createdAt: string;
}

const USERS_KEY = "pvd_users_login";
const SESSION_KEY = "pvd_session";

const DEFAULT_ADMIN: AppUser = {
  id: "usr_master",
  username: "pvd_master",
  password: "b72bfgfg",
  fullName: "PVD Master Admin",
  role: "super_admin",
  active: true,
  createdAt: new Date().toISOString(),
};

function loadUsers(): AppUser[] {
  try {
    const raw = localStorage.getItem(USERS_KEY);
    const users: AppUser[] = raw ? JSON.parse(raw) : [];
    if (!users.find((u) => u.id === DEFAULT_ADMIN.id)) {
      users.unshift(DEFAULT_ADMIN);
      localStorage.setItem(USERS_KEY, JSON.stringify(users));
    }
    return users;
  } catch {
    localStorage.setItem(USERS_KEY, JSON.stringify([DEFAULT_ADMIN]));
    return [DEFAULT_ADMIN];
  }
}

export function saveUsers(users: AppUser[]) {
  localStorage.setItem(USERS_KEY, JSON.stringify(users));
  window.dispatchEvent(new Event("pvd_users_changed"));
}

export function useUsers() {
  const [users, setUsers] = useState<AppUser[]>(loadUsers);
  const refresh = useCallback(() => setUsers(loadUsers()), []);
  useEffect(() => {
    window.addEventListener("pvd_users_changed", refresh);
    return () => window.removeEventListener("pvd_users_changed", refresh);
  }, [refresh]);
  return users;
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

// Auth context
interface AuthContextValue {
  user: AppUser | null;
  login: (username: string, password: string) => string | null;
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

  const login = useCallback((username: string, password: string): string | null => {
    const users = loadUsers();
    const found = users.find(
      (u) => u.username.toLowerCase() === username.toLowerCase() && u.password === password && u.active
    );
    if (!found) return "Invalid credentials or account disabled";
    localStorage.setItem(SESSION_KEY, JSON.stringify(found));
    setUser(found);
    return null;
  }, []);

  const logout = useCallback(() => {
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
