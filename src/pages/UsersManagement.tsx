import { useState } from "react";
import { useUsers, saveUsers, type AppUser, type UserRole, getRoleLabel } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { toast } from "sonner";
import { Plus, Pencil, Trash2, Users, ShieldCheck } from "lucide-react";

const ROLES: UserRole[] = ["super_admin", "data_entry", "inventory"];

const emptyForm = { username: "", password: "", fullName: "", role: "data_entry" as UserRole, active: true };

const UsersManagement = () => {
  const users = useUsers();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);

  const openAdd = () => {
    setEditingId(null);
    setForm(emptyForm);
    setDialogOpen(true);
  };

  const openEdit = (user: AppUser) => {
    setEditingId(user.id);
    setForm({ username: user.username, password: user.password, fullName: user.fullName, role: user.role, active: user.active });
    setDialogOpen(true);
  };

  const handleSave = () => {
    if (!form.username.trim() || !form.password.trim() || !form.fullName.trim()) {
      toast.error("All fields are required");
      return;
    }

    const all = [...users];

    if (editingId) {
      const idx = all.findIndex((u) => u.id === editingId);
      if (idx >= 0) {
        all[idx] = { ...all[idx], ...form };
        saveUsers(all);
        toast.success("User updated", { description: `UPDATE users_login SET ... WHERE username = '${form.username}'` });
      }
    } else {
      if (all.find((u) => u.username.toLowerCase() === form.username.toLowerCase())) {
        toast.error("Username already exists");
        return;
      }
      const newUser: AppUser = {
        id: `usr_${Date.now()}`,
        ...form,
        createdAt: new Date().toISOString(),
      };
      all.push(newUser);
      saveUsers(all);
      toast.success("User created", { description: `INSERT INTO users_login VALUES ('${form.username}', ...)` });
    }
    setDialogOpen(false);
  };

  const handleDelete = (id: string) => {
    if (id === "usr_master") {
      toast.error("Cannot delete the master admin");
      return;
    }
    const all = users.filter((u) => u.id !== id);
    saveUsers(all);
    setDeleteConfirm(null);
    toast.success("User deleted", { description: `DELETE FROM users_login WHERE id = '${id}'` });
  };

  const roleBadgeColor: Record<UserRole, string> = {
    super_admin: "bg-primary/20 text-primary border-primary/30",
    data_entry: "bg-blue-500/20 text-blue-400 border-blue-500/30",
    inventory: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-display font-bold gold-text flex items-center gap-2">
            <Users className="h-6 w-6" /> Users Management
          </h2>
          <p className="text-sm text-muted-foreground mt-1">Manage users_login table in Oracle Database</p>
        </div>
        <Button onClick={openAdd}>
          <Plus className="h-4 w-4 mr-1" /> Add User
        </Button>
      </div>

      <Card className="border-border">
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Username</TableHead>
                <TableHead>Full Name</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Created</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {users.map((user) => (
                <TableRow key={user.id}>
                  <TableCell className="font-mono text-sm flex items-center gap-2">
                    {user.id === "usr_master" && <ShieldCheck className="h-4 w-4 text-primary" />}
                    {user.username}
                  </TableCell>
                  <TableCell>{user.fullName}</TableCell>
                  <TableCell>
                    <Badge variant="outline" className={roleBadgeColor[user.role]}>
                      {getRoleLabel(user.role)}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline" className={user.active ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30" : "bg-destructive/20 text-destructive border-destructive/30"}>
                      {user.active ? "Active" : "Disabled"}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-muted-foreground text-sm">
                    {new Date(user.createdAt).toLocaleDateString()}
                  </TableCell>
                  <TableCell className="text-right space-x-2">
                    <Button variant="ghost" size="icon" onClick={() => openEdit(user)}>
                      <Pencil className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="text-destructive hover:text-destructive"
                      onClick={() => setDeleteConfirm(user.id)}
                      disabled={user.id === "usr_master"}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Add/Edit Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingId ? "Edit User" : "Add User"}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <Label>Username</Label>
              <Input value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} placeholder="e.g. john_doe" />
            </div>
            <div className="space-y-2">
              <Label>Full Name</Label>
              <Input value={form.fullName} onChange={(e) => setForm({ ...form, fullName: e.target.value })} placeholder="e.g. John Doe" />
            </div>
            <div className="space-y-2">
              <Label>Password</Label>
              <Input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} placeholder="Enter password" />
            </div>
            <div className="space-y-2">
              <Label>Role</Label>
              <Select value={form.role} onValueChange={(v) => setForm({ ...form, role: v as UserRole })}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {ROLES.map((r) => (
                    <SelectItem key={r} value={r}>{getRoleLabel(r)}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center justify-between">
              <Label>Active</Label>
              <Switch checked={form.active} onCheckedChange={(v) => setForm({ ...form, active: v })} />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>Cancel</Button>
            <Button onClick={handleSave}>{editingId ? "Update" : "Create"}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <Dialog open={!!deleteConfirm} onOpenChange={() => setDeleteConfirm(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirm Delete</DialogTitle>
          </DialogHeader>
          <p className="text-muted-foreground">Are you sure you want to delete this user? This action cannot be undone.</p>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteConfirm(null)}>Cancel</Button>
            <Button variant="destructive" onClick={() => deleteConfirm && handleDelete(deleteConfirm)}>Delete</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default UsersManagement;
