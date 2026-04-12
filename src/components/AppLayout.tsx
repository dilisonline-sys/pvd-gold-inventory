import { NavLink, Outlet } from "react-router-dom";
import { Database, PlusCircle, Package, Settings, Users, LogOut } from "lucide-react";
import { useAuth, canAccessRoute, getRoleLabel } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

const allNavItems = [
  { to: "/", icon: Package, label: "Inventory" },
  { to: "/data-entry", icon: PlusCircle, label: "Data Entry" },
  { to: "/settings", icon: Settings, label: "Connection" },
  { to: "/users", icon: Users, label: "Users" },
];

const AppLayout = () => {
  const { user, logout } = useAuth();

  const navItems = allNavItems.filter((item) =>
    user ? canAccessRoute(user.role, item.to) : false
  );

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-border px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Database className="h-7 w-7 text-primary" />
          <h1 className="text-2xl font-display font-bold gold-text">PVD Gold</h1>
        </div>
        <nav className="flex items-center gap-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                `flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:text-foreground hover:bg-secondary"
                }`
              }
            >
              <item.icon className="h-4 w-4" />
              {item.label}
            </NavLink>
          ))}
        </nav>
        {user && (
          <div className="flex items-center gap-3">
            <div className="text-right">
              <p className="text-sm font-medium">{user.fullName}</p>
              <Badge variant="outline" className="text-xs">{getRoleLabel(user.role)}</Badge>
            </div>
            <Button variant="ghost" size="icon" onClick={logout} title="Logout">
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        )}
      </header>
      <main className="flex-1 p-6">
        <Outlet />
      </main>
    </div>
  );
};

export default AppLayout;
