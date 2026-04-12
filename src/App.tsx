import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes, Navigate } from "react-router-dom";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { AuthProvider, useAuth, canAccessRoute } from "@/lib/auth";
import AppLayout from "./components/AppLayout";
import InventoryView from "./pages/InventoryView";
import DataEntry from "./pages/DataEntry";
import ConnectionSettings from "./pages/ConnectionSettings";
import UsersManagement from "./pages/UsersManagement";
import Login from "./pages/Login";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

function ProtectedRoute({ path, children }: { path: string; children: React.ReactNode }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  if (!canAccessRoute(user.role, path)) return <Navigate to="/" replace />;
  return <>{children}</>;
}

function AuthGate({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function LoginGate() {
  const { user } = useAuth();
  if (user) return <Navigate to="/" replace />;
  return <Login />;
}

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<LoginGate />} />
            <Route element={<AuthGate><AppLayout /></AuthGate>}>
              <Route path="/" element={<ProtectedRoute path="/"><InventoryView /></ProtectedRoute>} />
              <Route path="/data-entry" element={<ProtectedRoute path="/data-entry"><DataEntry /></ProtectedRoute>} />
              <Route path="/settings" element={<ProtectedRoute path="/settings"><ConnectionSettings /></ProtectedRoute>} />
              <Route path="/users" element={<ProtectedRoute path="/users"><UsersManagement /></ProtectedRoute>} />
            </Route>
            <Route path="*" element={<NotFound />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
