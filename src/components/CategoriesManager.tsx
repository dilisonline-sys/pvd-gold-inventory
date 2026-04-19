import { useState } from "react";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";
import { Tags, Plus, Pencil, Trash2, Check, X, Loader2 } from "lucide-react";
import { useCategories, addCategory, updateCategory, deleteCategory, type Category } from "@/lib/categories";

interface Props {
  triggerLabel?: string;
}

const CategoriesManager = ({ triggerLabel = "Manage Categories" }: Props) => {
  const [open, setOpen] = useState(false);
  const { categories, loading } = useCategories();
  const [newName, setNewName] = useState("");
  const [adding, setAdding] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState("");
  const [busyId, setBusyId] = useState<string | null>(null);

  const handleAdd = async () => {
    if (!newName.trim()) return;
    setAdding(true);
    try {
      await addCategory(newName.trim());
      toast.success("Category added");
      setNewName("");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to add");
    } finally {
      setAdding(false);
    }
  };

  const startEdit = (c: Category) => {
    setEditingId(c.id);
    setEditName(c.name);
  };

  const saveEdit = async (c: Category) => {
    if (!editName.trim() || editName.trim() === c.name) {
      setEditingId(null);
      return;
    }
    setBusyId(c.id);
    try {
      await updateCategory(c.id, editName.trim());
      toast.success("Category renamed");
      setEditingId(null);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to update");
    } finally {
      setBusyId(null);
    }
  };

  const handleDelete = async (c: Category) => {
    if (!confirm(`Delete category "${c.name}"? Existing items keep their category text.`)) return;
    setBusyId(c.id);
    try {
      await deleteCategory(c.id);
      toast.success("Category deleted");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to delete");
    } finally {
      setBusyId(null);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" className="gap-2">
          <Tags className="h-4 w-4" />
          {triggerLabel}
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Manage Categories</DialogTitle>
          <DialogDescription>
            Add, rename or remove categories. Renames update existing items and products.
          </DialogDescription>
        </DialogHeader>

        <div className="flex gap-2 pt-2">
          <Input
            placeholder="New category name"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAdd()}
          />
          <Button onClick={handleAdd} disabled={adding || !newName.trim()}>
            {adding ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
          </Button>
        </div>

        <div className="max-h-[50vh] overflow-y-auto space-y-1.5 pt-2">
          {loading ? (
            <div className="text-center text-sm text-muted-foreground py-4">
              <Loader2 className="h-4 w-4 animate-spin inline mr-2" /> Loading…
            </div>
          ) : categories.length === 0 ? (
            <p className="text-center text-sm text-muted-foreground py-4">No categories yet</p>
          ) : (
            categories.map((c) => (
              <div key={c.id} className="flex items-center gap-2 px-3 py-2 rounded-md border border-border bg-card">
                {editingId === c.id ? (
                  <>
                    <Input
                      value={editName}
                      onChange={(e) => setEditName(e.target.value)}
                      className="h-8"
                      autoFocus
                      onKeyDown={(e) => {
                        if (e.key === "Enter") saveEdit(c);
                        if (e.key === "Escape") setEditingId(null);
                      }}
                    />
                    <Button size="icon" variant="ghost" className="h-8 w-8" onClick={() => saveEdit(c)} disabled={busyId === c.id}>
                      <Check className="h-4 w-4 text-emerald-500" />
                    </Button>
                    <Button size="icon" variant="ghost" className="h-8 w-8" onClick={() => setEditingId(null)}>
                      <X className="h-4 w-4" />
                    </Button>
                  </>
                ) : (
                  <>
                    <span className="flex-1 text-sm">{c.name}</span>
                    <Button size="icon" variant="ghost" className="h-8 w-8" onClick={() => startEdit(c)} disabled={busyId === c.id}>
                      <Pencil className="h-3.5 w-3.5" />
                    </Button>
                    <Button
                      size="icon"
                      variant="ghost"
                      className="h-8 w-8 text-destructive hover:text-destructive"
                      onClick={() => handleDelete(c)}
                      disabled={busyId === c.id}
                    >
                      {busyId === c.id ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Trash2 className="h-3.5 w-3.5" />}
                    </Button>
                  </>
                )}
              </div>
            ))
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default CategoriesManager;
