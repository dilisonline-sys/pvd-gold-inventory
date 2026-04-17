import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { toast } from "sonner";
import { Database, CheckCircle2, XCircle, Loader2, TableProperties } from "lucide-react";
import { apiFetch } from "@/lib/api";

const PG_CONFIG_KEY = "pvd_pg_config";

export interface PgConfig {
  host: string;
  port: string;
  database: string;
  schema: string;
  username: string;
  password: string;
  ssl: boolean;
}

export function loadPgConfig(): PgConfig {
  try {
    const raw = localStorage.getItem(PG_CONFIG_KEY);
    return raw
      ? JSON.parse(raw)
      : { host: "", port: "5432", database: "", schema: "pvd_schema", username: "", password: "", ssl: false };
  } catch {
    return { host: "", port: "5432", database: "", schema: "pvd_schema", username: "", password: "", ssl: false };
  }
}

interface ConnectionResult {
  database: string;
  schema: string;
  tables: string[];
}

const ConnectionSettings = () => {
  const [config, setConfig] = useState<PgConfig>(loadPgConfig);
  const [status, setStatus] = useState<"idle" | "testing" | "connected" | "error">("idle");
  const [connectionResult, setConnectionResult] = useState<ConnectionResult | null>(null);
  const [errorMessage, setErrorMessage] = useState("");

  const handleChange = (field: keyof PgConfig, value: string | boolean) => {
    setConfig((prev) => ({ ...prev, [field]: value }));
  };

  const handleTestConnection = async () => {
    if (!config.host || !config.database || !config.username || !config.password) {
      toast.error("Please fill in all required fields");
      return;
    }
    setStatus("testing");
    setConnectionResult(null);
    setErrorMessage("");

    try {
      const result = await apiFetch<ConnectionResult>("/api/test-connection", {
        method: "POST",
        body: JSON.stringify(config),
      });
      setConnectionResult(result);
      setStatus("connected");
      toast.success(`Connected to ${result.database} → ${result.schema}`);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Connection failed";
      setErrorMessage(msg);
      setStatus("error");
      toast.error(msg);
    }
  };

  const handleSave = () => {
    localStorage.setItem(PG_CONFIG_KEY, JSON.stringify(config));
    toast.success("Connection settings saved");
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h2 className="text-3xl font-display font-bold gold-text">Database Connection</h2>
        <p className="text-muted-foreground mt-1">Configure your PostgreSQL database connection</p>
      </div>

      <Card className="gold-glow">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5 text-primary" />
            PostgreSQL Database
          </CardTitle>
          <CardDescription>Enter your PostgreSQL database connection details below</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="host">Host / IP Address *</Label>
              <Input
                id="host"
                placeholder="localhost or 192.168.1.100"
                value={config.host}
                onChange={(e) => handleChange("host", e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="port">Port</Label>
              <Input
                id="port"
                placeholder="5432"
                value={config.port}
                onChange={(e) => handleChange("port", e.target.value)}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="database">Database Name *</Label>
              <Input
                id="database"
                placeholder="pvd_jewelry"
                value={config.database}
                onChange={(e) => handleChange("database", e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="schema">Schema</Label>
              <Input
                id="schema"
                placeholder="pvd_schema"
                value={config.schema}
                onChange={(e) => handleChange("schema", e.target.value)}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="username">Username *</Label>
              <Input
                id="username"
                placeholder="postgres"
                value={config.username}
                onChange={(e) => handleChange("username", e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password *</Label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={config.password}
                onChange={(e) => handleChange("password", e.target.value)}
              />
            </div>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="ssl"
              checked={config.ssl}
              onChange={(e) => handleChange("ssl", e.target.checked)}
              className="rounded border-border"
            />
            <Label htmlFor="ssl" className="cursor-pointer">Use SSL connection</Label>
          </div>

          {/* Connection Status */}
          {status !== "idle" && (
            <div
              className={`flex items-center gap-2 p-3 rounded-md text-sm ${
                status === "testing"
                  ? "bg-secondary text-muted-foreground"
                  : status === "connected"
                  ? "bg-primary/10 text-primary"
                  : "bg-destructive/10 text-destructive"
              }`}
            >
              {status === "testing" && <Loader2 className="h-4 w-4 animate-spin" />}
              {status === "connected" && <CheckCircle2 className="h-4 w-4" />}
              {status === "error" && <XCircle className="h-4 w-4" />}
              {status === "testing" && "Testing connection..."}
              {status === "connected" && "Connection successful"}
              {status === "error" && errorMessage || "Connection failed. Check your settings."}
            </div>
          )}

          <div className="flex gap-3 pt-2">
            <Button variant="outline" onClick={handleTestConnection} disabled={status === "testing"}>
              {status === "testing" ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : null}
              Test Connection
            </Button>
            <Button onClick={handleSave}>Save Settings</Button>
          </div>
        </CardContent>
      </Card>

      {/* Connection Result — DB, Schema, and Tables */}
      {connectionResult && (
        <Card className="gold-glow">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TableProperties className="h-5 w-5 text-primary" />
              Connection Details
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="rounded-md border border-border p-3">
                <p className="text-xs text-muted-foreground uppercase tracking-wide">Database</p>
                <p className="text-lg font-semibold text-foreground">{connectionResult.database}</p>
              </div>
              <div className="rounded-md border border-border p-3">
                <p className="text-xs text-muted-foreground uppercase tracking-wide">Schema</p>
                <p className="text-lg font-semibold text-foreground">{connectionResult.schema}</p>
              </div>
            </div>

            <div>
              <p className="text-sm font-medium text-muted-foreground mb-2">
                Tables in <span className="text-primary">{connectionResult.schema}</span> ({connectionResult.tables.length})
              </p>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-12">#</TableHead>
                    <TableHead>Table Name</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {connectionResult.tables.map((table, idx) => (
                    <TableRow key={table}>
                      <TableCell className="text-muted-foreground">{idx + 1}</TableCell>
                      <TableCell className="font-mono text-sm">{table}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default ConnectionSettings;
