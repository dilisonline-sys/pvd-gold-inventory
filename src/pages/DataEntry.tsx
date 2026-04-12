import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { PlusCircle, RotateCcw, Columns3, Trash2, ImagePlus } from "lucide-react";
import { categories, karatOptions, statusOptions } from "@/lib/mockData";
import { useCustomColumns, addCustomColumn, removeCustomColumn, type CustomColumn } from "@/lib/customColumns";

const initialForm = {
  itemName: "",
  category: "",
  karat: "",
  weightGrams: "",
  quantity: "",
  status: "In Stock" as string,
  image: null as File | null,
};

const DataEntry = () => {
  const [form, setForm] = useState(initialForm);
  const [customValues, setCustomValues] = useState<Record<string, string>>({});
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const customColumns = useCustomColumns();

  // New column dialog state
  const [dialogOpen, setDialogOpen] = useState(false);
  const [newCol, setNewCol] = useState({ name: "", type: "TEXT" as CustomColumn["type"], required: false });

  const handleChange = (field: string, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleCustomChange = (colId: string, value: string) => {
    setCustomValues((prev) => ({ ...prev, [colId]: value }));
  };

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setForm((prev) => ({ ...prev, image: file }));
      const reader = new FileReader();
      reader.onloadend = () => setImagePreview(reader.result as string);
      reader.readAsDataURL(file);
    }
  };

  const handleAddColumn = () => {
    if (!newCol.name.trim()) {
      toast.error("Column name is required");
      return;
    }
    addCustomColumn(newCol);
    toast.success(`Column "${newCol.name}" added — ALTER TABLE mock committed to Oracle`, {
      description: `ALTER TABLE PVD_INVENTORY ADD (${newCol.name.toUpperCase().replace(/\s+/g, "_")} ${newCol.type === "BLOB" ? "BLOB" : newCol.type === "NUMBER" ? "NUMBER" : newCol.type === "DATE" ? "DATE" : "VARCHAR2(255)"});`,
    });
    setNewCol({ name: "", type: "TEXT", required: false });
    setDialogOpen(false);
  };

  const handleRemoveColumn = (col: CustomColumn) => {
    removeCustomColumn(col.id);
    toast.success(`Column "${col.name}" removed`, {
      description: `ALTER TABLE PVD_INVENTORY DROP COLUMN ${col.name.toUpperCase().replace(/\s+/g, "_")};`,
    });
    setCustomValues((prev) => {
      const next = { ...prev };
      delete next[col.id];
      return next;
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.itemName || !form.category || !form.karat || !form.weightGrams) {
      toast.error("Please fill in all required fields");
      return;
    }
    // Check required custom fields
    for (const col of customColumns) {
      if (col.required && !customValues[col.id]) {
        toast.error(`"${col.name}" is required`);
        return;
      }
    }
    toast.success(`"${form.itemName}" added to inventory (mock)`, {
      description: "INSERT INTO PVD_INVENTORY (...) VALUES (...) — committed",
    });
    setForm(initialForm);
    setCustomValues({});
    setImagePreview(null);
  };

  const handleReset = () => {
    setForm(initialForm);
    setCustomValues({});
    setImagePreview(null);
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-display font-bold gold-text">Data Entry</h2>
          <p className="text-muted-foreground mt-1">Add new jewelry items to the Oracle database</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button variant="outline" className="gap-2">
              <Columns3 className="h-4 w-4" />
              Add Column
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add Column to PVD_INVENTORY</DialogTitle>
              <DialogDescription>
                This will execute an ALTER TABLE statement on the Oracle database to add a new column.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-2">
              <div className="space-y-2">
                <Label>Column Name *</Label>
                <Input
                  placeholder="e.g. Stone Type"
                  value={newCol.name}
                  onChange={(e) => setNewCol((p) => ({ ...p, name: e.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <Label>Data Type</Label>
                <Select value={newCol.type} onValueChange={(v) => setNewCol((p) => ({ ...p, type: v as CustomColumn["type"] }))}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="TEXT">VARCHAR2 (Text)</SelectItem>
                    <SelectItem value="NUMBER">NUMBER</SelectItem>
                    <SelectItem value="DATE">DATE</SelectItem>
                    <SelectItem value="BLOB">BLOB (Image/File)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="colRequired"
                  checked={newCol.required}
                  onChange={(e) => setNewCol((p) => ({ ...p, required: e.target.checked }))}
                  className="rounded border-border"
                />
                <Label htmlFor="colRequired" className="cursor-pointer">Required (NOT NULL)</Label>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setDialogOpen(false)}>Cancel</Button>
              <Button onClick={handleAddColumn}>
                <PlusCircle className="h-4 w-4 mr-2" />
                Add Column
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Active custom columns */}
      {customColumns.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {customColumns.map((col) => (
            <Badge key={col.id} variant="outline" className="gap-1.5 py-1 px-3 bg-primary/5 border-primary/20">
              {col.name}
              <span className="text-[10px] text-muted-foreground">({col.type})</span>
              <button onClick={() => handleRemoveColumn(col)} className="ml-1 hover:text-destructive transition-colors">
                <Trash2 className="h-3 w-3" />
              </button>
            </Badge>
          ))}
        </div>
      )}

      <Card className="gold-glow">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <PlusCircle className="h-5 w-5 text-primary" />
            New Jewelry Item
          </CardTitle>
          <CardDescription>Fill in the details below to add a new item to inventory</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Row 1 */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="itemName">Item Name *</Label>
                <Input
                  id="itemName"
                  placeholder="e.g. Cuban Link Chain 22&quot;"
                  value={form.itemName}
                  onChange={(e) => handleChange("itemName", e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label>Category *</Label>
                <Select value={form.category} onValueChange={(v) => handleChange("category", v)}>
                  <SelectTrigger><SelectValue placeholder="Select category" /></SelectTrigger>
                  <SelectContent>
                    {categories.map((c) => (
                      <SelectItem key={c} value={c}>{c}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Row 2 */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label>Karat *</Label>
                <Select value={form.karat} onValueChange={(v) => handleChange("karat", v)}>
                  <SelectTrigger><SelectValue placeholder="Select karat" /></SelectTrigger>
                  <SelectContent>
                    {karatOptions.map((k) => (
                      <SelectItem key={k} value={String(k)}>{k}K</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="weight">Weight (grams) *</Label>
                <Input
                  id="weight"
                  type="number"
                  step="0.1"
                  placeholder="0.0"
                  value={form.weightGrams}
                  onChange={(e) => handleChange("weightGrams", e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="quantity">Quantity</Label>
                <Input
                  id="quantity"
                  type="number"
                  placeholder="1"
                  value={form.quantity}
                  onChange={(e) => handleChange("quantity", e.target.value)}
                />
              </div>
            </div>

            {/* Row 3 */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Status</Label>
                <Select value={form.status} onValueChange={(v) => handleChange("status", v)}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {statusOptions.map((s) => (
                      <SelectItem key={s} value={s}>{s}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Image Upload (BLOB) */}
            <div className="space-y-2">
              <Label>Item Image (BLOB)</Label>
              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2 px-4 py-2 border border-dashed border-primary/30 rounded-md cursor-pointer hover:bg-primary/5 transition-colors">
                  <ImagePlus className="h-4 w-4 text-primary" />
                  <span className="text-sm">Choose image...</span>
                  <input type="file" accept="image/*" className="hidden" onChange={handleImageChange} />
                </label>
                {imagePreview && (
                  <div className="relative">
                    <img src={imagePreview} alt="Preview" className="h-16 w-16 rounded-md object-cover border border-border" />
                    <button
                      type="button"
                      onClick={() => { setImagePreview(null); setForm((p) => ({ ...p, image: null })); }}
                      className="absolute -top-1.5 -right-1.5 bg-destructive text-destructive-foreground rounded-full h-4 w-4 flex items-center justify-center text-xs"
                    >×</button>
                  </div>
                )}
              </div>
              <p className="text-xs text-muted-foreground">Stored as BLOB in Oracle — rendered from base64 in inventory view</p>
            </div>

            {/* Custom columns */}
            {customColumns.length > 0 && (
              <div className="space-y-3 pt-2 border-t border-border">
                <p className="text-sm font-medium text-muted-foreground">Custom Fields</p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {customColumns.map((col) => (
                    <div key={col.id} className="space-y-2">
                      <Label>
                        {col.name} {col.required && "*"}
                        <span className="text-xs text-muted-foreground ml-1">({col.type})</span>
                      </Label>
                      {col.type === "BLOB" ? (
                        <label className="flex items-center gap-2 px-4 py-2 border border-dashed border-primary/30 rounded-md cursor-pointer hover:bg-primary/5 transition-colors text-sm">
                          <ImagePlus className="h-4 w-4 text-primary" />
                          Choose file...
                          <input
                            type="file"
                            className="hidden"
                            onChange={(e) => {
                              const file = e.target.files?.[0];
                              if (file) handleCustomChange(col.id, file.name);
                            }}
                          />
                        </label>
                      ) : (
                        <Input
                          type={col.type === "NUMBER" ? "number" : col.type === "DATE" ? "date" : "text"}
                          placeholder={col.name}
                          value={customValues[col.id] || ""}
                          onChange={(e) => handleCustomChange(col.id, e.target.value)}
                        />
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="flex gap-3 pt-2">
              <Button type="submit">
                <PlusCircle className="h-4 w-4 mr-2" />
                Add Item
              </Button>
              <Button type="button" variant="outline" onClick={handleReset}>
                <RotateCcw className="h-4 w-4 mr-2" />
                Reset
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

export default DataEntry;
