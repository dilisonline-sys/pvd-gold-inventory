import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogTitle, DialogHeader, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Search, Tag, ImageOff, Loader2, Trash2, Layers } from "lucide-react";
import { toast } from "sonner";
import { useProducts, deleteProduct, type Product } from "@/lib/products";
import { useCategories } from "@/lib/categories";
import { useAuth } from "@/lib/auth";
import CategoriesManager from "@/components/CategoriesManager";

const ProductsView = () => {
  const [search, setSearch] = useState("");
  const [filterCategory, setFilterCategory] = useState("all");
  const [lightboxImg, setLightboxImg] = useState<string | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<Product | null>(null);
  const [deleting, setDeleting] = useState(false);
  const { products, loading, error } = useProducts();
  const { categories } = useCategories();
  const { user } = useAuth();
  const isSuperAdmin = user?.role === "super_admin";
  const canManageCats = isSuperAdmin || user?.role === "data_entry";

  const handleDelete = async () => {
    if (!deleteConfirm) return;
    setDeleting(true);
    try {
      await deleteProduct(deleteConfirm.id);
      toast.success("Product deleted");
      setDeleteConfirm(null);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Delete failed");
    } finally {
      setDeleting(false);
    }
  };

  const filtered = products.filter((p) => {
    const q = search.toLowerCase();
    const matchesSearch =
      p.productName.toLowerCase().includes(q) ||
      (p.sku || "").toLowerCase().includes(q);
    const matchesCategory = filterCategory === "all" || p.category === filterCategory;
    return matchesSearch && matchesCategory;
  });

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div>
          <h2 className="text-3xl font-display font-bold gold-text">Products</h2>
          <p className="text-muted-foreground mt-1">Catalog of jewelry products</p>
        </div>
        {canManageCats && <CategoriesManager />}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Card className="gold-glow">
          <CardContent className="flex items-center gap-3 py-4">
            <div className="p-2 rounded-md bg-primary/10">
              <Layers className="h-5 w-5 text-primary" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Total Products</p>
              <p className="text-xl font-display font-bold">{filtered.length}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search by name or SKU..."
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
            <img src={lightboxImg} alt="Product" className="w-full rounded-md object-contain max-h-[70vh]" />
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
            <Tag className="h-4 w-4 text-primary" />
            {filtered.length} product{filtered.length !== 1 ? "s" : ""}
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-4">
          <div className="rounded-md border overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-16">Image</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>SKU</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead className="text-right">Karat</TableHead>
                  <TableHead className="text-right">Price</TableHead>
                  {isSuperAdmin && <TableHead className="text-right w-16">Actions</TableHead>}
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  <TableRow>
                    <TableCell colSpan={6 + (isSuperAdmin ? 1 : 0)} className="text-center text-muted-foreground py-8">
                      <Loader2 className="h-4 w-4 animate-spin inline mr-2" /> Loading…
                    </TableCell>
                  </TableRow>
                ) : filtered.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6 + (isSuperAdmin ? 1 : 0)} className="text-center text-muted-foreground py-8">
                      No products found
                    </TableCell>
                  </TableRow>
                ) : (
                  filtered.map((p) => (
                    <TableRow key={p.id}>
                      <TableCell>
                        {p.imageUrl ? (
                          <button onClick={() => setLightboxImg(p.imageUrl!)} className="block">
                            <img
                              src={p.imageUrl}
                              alt={p.productName}
                              className="h-10 w-10 rounded object-cover border border-border hover:ring-2 hover:ring-primary/50 transition-all cursor-pointer"
                            />
                          </button>
                        ) : (
                          <div className="h-10 w-10 rounded bg-muted flex items-center justify-center">
                            <ImageOff className="h-4 w-4 text-muted-foreground" />
                          </div>
                        )}
                      </TableCell>
                      <TableCell className="font-medium">{p.productName}</TableCell>
                      <TableCell className="font-mono text-xs text-muted-foreground">{p.sku || "—"}</TableCell>
                      <TableCell>{p.category}</TableCell>
                      <TableCell className="text-right">{p.karat}K</TableCell>
                      <TableCell className="text-right">{p.price != null ? `$${p.price.toFixed(2)}` : "—"}</TableCell>
                      {isSuperAdmin && (
                        <TableCell className="text-right">
                          <Button
                            variant="ghost"
                            size="icon"
                            className="text-destructive hover:text-destructive"
                            onClick={() => setDeleteConfirm(p)}
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
            <DialogTitle>Delete product?</DialogTitle>
          </DialogHeader>
          <p className="text-muted-foreground">
            This will permanently delete <span className="font-medium text-foreground">{deleteConfirm?.productName}</span>.
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

export default ProductsView;
