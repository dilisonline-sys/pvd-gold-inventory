import { useState, useMemo } from "react";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogTitle, DialogHeader, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Search, Package, Weight, Layers, ImageOff, Loader2, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { useCustomColumns } from "@/lib/customColumns";
import { useItems, deleteItem, type JewelryItem } from "@/lib/items";
import { useAuth } from "@/lib/auth";
import { useCategories } from "@/lib/categories";
import CategoriesManager from "@/components/CategoriesManager";

const statusColor: Record<JewelryItem["status"], string> = {
  "In Stock": "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  "Sold": "bg-muted text-muted-foreground border-border",
  "On Display": "bg-primary/15 text-primary border-primary/30",
  "Reserved": "bg-amber-500/15 text-amber-400 border-amber-500/30",
};

const InventoryView = () => {
  const [search, setSearch] = useState("");
  const [filterCategory, setFilterCategory] = useState("all");
  const [lightboxImg, setLightboxImg] = useState<string | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<JewelryItem | null>(null);
  const [deleting, setDeleting] = useState(false);
  const customColumns = useCustomColumns();
  const { items, loading, error } = useItems();
  const { user } = useAuth();
  const { categories } = useCategories();
  const isSuperAdmin = user?.role === "super_admin";
  const canManageCats = isSuperAdmin || user?.role === "data_entry";

  const handleDelete = async () => {
    if (!deleteConfirm) return;
    setDeleting(true);
    try {
      await deleteItem(deleteConfirm.id);
      toast.success("Item deleted");
      setDeleteConfirm(null);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Delete failed");
    } finally {
      setDeleting(false);
    }
  };

  const filtered = items.filter((item) => {
    const matchesSearch =
      item.itemName.toLowerCase().includes(search.toLowerCase()) ||
      item.id.toLowerCase().includes(search.toLowerCase());
    const matchesCategory = filterCategory === "all" || item.category === filterCategory;
    return matchesSearch && matchesCategory;
  });

  const totalItems = filtered.reduce((sum, i) => sum + i.quantity, 0);

  // Subtotal weight per karat
  const weightByKarat = useMemo(() => {
    const map = new Map<number, number>();
    for (const i of filtered) {
      map.set(i.karat, (map.get(i.karat) || 0) + i.weightGrams * i.quantity);
    }
    return Array.from(map.entries()).sort((a, b) => b[0] - a[0]);
  }, [filtered]);

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div>
          <h2 className="text-3xl font-display font-bold gold-text">Inventory</h2>
          <p className="text-muted-foreground mt-1">Browse jewelry items from PostgreSQL</p>
        </div>
        {canManageCats && <CategoriesManager />}
      </div>

      {/* Total Items + per-karat subtotal cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
        <Card className="gold-glow">
          <CardContent className="flex items-center gap-3 py-4">
            <div className="p-2 rounded-md bg-primary/10">
              <Layers className="h-5 w-5 text-primary" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Total Items</p>
              <p className="text-xl font-display font-bold">{totalItems}</p>
            </div>
          </CardContent>
        </Card>
        {weightByKarat.length === 0 ? (
          <Card>
            <CardContent className="flex items-center gap-3 py-4">
              <div className="p-2 rounded-md bg-muted">
                <Weight className="h-5 w-5 text-muted-foreground" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Weight</p>
                <p className="text-xl font-display font-bold">0g</p>
              </div>
            </CardContent>
          </Card>
        ) : (
          weightByKarat.map(([karat, weight]) => (
            <Card key={karat}>
              <CardContent className="flex items-center gap-3 py-4">
                <div className="p-2 rounded-md bg-primary/10">
                  <Weight className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">{karat}K Subtotal</p>
                  <p className="text-xl font-display font-bold">{weight.toFixed(1)}g</p>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search by name or ID..."
            className="pl-9"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <Select value={filterCategory} onValueChange={setFilterCategory}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Category" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Categories</SelectItem>
            {categories.map((c) => (
              <SelectItem key={c.id} value={c.name}>{c.name}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <Dialog open={!!lightboxImg} onOpenChange={() => setLightboxImg(null)}>
        <DialogContent className="max-w-lg p-2">
          <DialogTitle className="sr-only">Image Preview</DialogTitle>
          {lightboxImg && (
            <img src={lightboxImg} alt="Jewelry item" className="w-full rounded-md object-contain max-h-[70vh]" />
          )}
        </DialogContent>
      </Dialog>

      {error && (
        <div className="bg-destructive/10 border border-destructive/30 text-destructive text-sm rounded-md p-3">
          {error}
        </div>
      )}

      <Card>
        <CardHeader className="pb-0">
          <CardTitle className="flex items-center gap-2 text-base">
            <Package className="h-4 w-4 text-primary" />
            {filtered.length} item{filtered.length !== 1 ? "s" : ""}
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-4">
          <div className="rounded-md border overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-16">Image</TableHead>
                  <TableHead className="w-24">ID</TableHead>
                  <TableHead>Item</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead className="text-right">Karat</TableHead>
                  <TableHead className="text-right">Weight</TableHead>
                  <TableHead className="text-right">Qty</TableHead>
                  <TableHead>Status</TableHead>
                  {customColumns.map((col) => (
                    <TableHead key={col.id}>{col.name}</TableHead>
                  ))}
                  {isSuperAdmin && <TableHead className="text-right w-16">Actions</TableHead>}
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  <TableRow>
                    <TableCell colSpan={8 + customColumns.length + (isSuperAdmin ? 1 : 0)} className="text-center text-muted-foreground py-8">
                      <Loader2 className="h-4 w-4 animate-spin inline mr-2" /> Loading…
                    </TableCell>
                  </TableRow>
                ) : filtered.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={8 + customColumns.length + (isSuperAdmin ? 1 : 0)} className="text-center text-muted-foreground py-8">
                      No items found
                    </TableCell>
                  </TableRow>
                ) : (
                  filtered.map((item) => (
                    <TableRow key={item.id}>
                      <TableCell>
                        {item.imageUrl ? (
                          <button onClick={() => setLightboxImg(item.imageUrl!)} className="block">
                            <img
                              src={item.imageUrl}
                              alt={item.itemName}
                              className="h-10 w-10 rounded object-cover border border-border hover:ring-2 hover:ring-primary/50 transition-all cursor-pointer"
                            />
                          </button>
                        ) : (
                          <div className="h-10 w-10 rounded bg-muted flex items-center justify-center">
                            <ImageOff className="h-4 w-4 text-muted-foreground" />
                          </div>
                        )}
                      </TableCell>
                      <TableCell className="font-mono text-xs text-muted-foreground">{item.id.slice(0, 8)}</TableCell>
                      <TableCell className="font-medium">{item.itemName}</TableCell>
                      <TableCell>{item.category}</TableCell>
                      <TableCell className="text-right">{item.karat}K</TableCell>
                      <TableCell className="text-right">{item.weightGrams}g</TableCell>
                      <TableCell className="text-right">{item.quantity}</TableCell>
                      <TableCell>
                        <Badge variant="outline" className={statusColor[item.status]}>
                          {item.status}
                        </Badge>
                      </TableCell>
                      {customColumns.map((col) => (
                        <TableCell key={col.id} className="text-muted-foreground text-sm">
                          {item.customFields?.[col.id] || "—"}
                        </TableCell>
                      ))}
                      {isSuperAdmin && (
                        <TableCell className="text-right">
                          <Button
                            variant="ghost"
                            size="icon"
                            className="text-destructive hover:text-destructive"
                            onClick={() => setDeleteConfirm(item)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </TableCell>
                      )}
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      <Dialog open={!!deleteConfirm} onOpenChange={(o) => !o && setDeleteConfirm(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete item?</DialogTitle>
          </DialogHeader>
          <p className="text-muted-foreground">
            This will permanently delete <span className="font-medium text-foreground">{deleteConfirm?.itemName}</span>. This action cannot be undone.
          </p>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteConfirm(null)} disabled={deleting}>Cancel</Button>
            <Button variant="destructive" onClick={handleDelete} disabled={deleting}>
              {deleting && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default InventoryView;
