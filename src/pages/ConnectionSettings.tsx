import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "sonner";
import { Database, CheckCircle2, XCircle, Loader2 } from "lucide-react";

const ConnectionSettings = () => {
  const [config, setConfig] = useState({
    host: "",
    port: "1521",
    serviceName: "",
    username: "",
    password: "",
  });
  const [status, setStatus] = useState<"idle" | "testing" | "connected" | "error">("idle");

  const handleChange = (field: string, value: string) => {
    setConfig((prev) => ({ ...prev, [field]: value }));
  };

  const handleTestConnection = () => {
    if (!config.host || !config.serviceName || !config.username || !config.password) {
      toast.error("Please fill in all required fields");
      return;
    }
    setStatus("testing");
    setTimeout(() => {
      setStatus("connected");
      toast.success("Connection successful (mock)");
    }, 1500);
  };

  const handleSave = () => {
    localStorage.setItem("pvd_oracle_config", JSON.stringify(config));
    toast.success("Connection settings saved");
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h2 className="text-3xl font-display font-bold gold-text">Database Connection</h2>
        <p className="text-muted-foreground mt-1">Configure your Oracle database connection</p>
      </div>

      <Card className="gold-glow">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5 text-primary" />
            Oracle Database
          </CardTitle>
          <CardDescription>Enter your Oracle database connection details below</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="host">Host / IP Address *</Label>
              <Input
                id="host"
                placeholder="192.168.1.100"
                value={config.host}
                onChange={(e) => handleChange("host", e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="port">Port</Label>
              <Input
                id="port"
                placeholder="1521"
                value={config.port}
                onChange={(e) => handleChange("port", e.target.value)}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="serviceName">Service Name / SID *</Label>
            <Input
              id="serviceName"
              placeholder="ORCL"
              value={config.serviceName}
              onChange={(e) => handleChange("serviceName", e.target.value)}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="username">Username *</Label>
              <Input
                id="username"
                placeholder="pvd_admin"
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
              {status === "error" && "Connection failed. Check your settings."}
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
    </div>
  );
};

export default ConnectionSettings;
