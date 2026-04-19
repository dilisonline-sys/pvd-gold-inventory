import { useState, useEffect, useCallback } from "react";
import { apiFetch } from "@/lib/api";

export interface ApiJewelryItem {
  id: string;
  item_name: string;
  category: string;
  karat: number;
  weight_grams: number;
  quantity: number;
  status: string;
  image_url: string | null;
  date_added: string;
}

export interface JewelryItem {
  id: string;
  itemName: string;
  category: string;
  karat: number;
  weightGrams: number;
  quantity: number;
  status: "In Stock" | "Sold" | "On Display" | "Reserved";
  imageUrl?: string;
  dateAdded: string;
  customFields?: Record<string, string>;
}

function fromApi(i: ApiJewelryItem): JewelryItem {
  return {
    id: i.id,
    itemName: i.item_name,
    category: i.category,
    karat: Number(i.karat),
    weightGrams: Number(i.weight_grams),
    quantity: i.quantity,
    status: i.status as JewelryItem["status"],
    imageUrl: i.image_url || undefined,
    dateAdded: i.date_added,
  };
}

const CHANGED = "pvd_items_changed";

export async function createItem(input: Omit<JewelryItem, "id" | "dateAdded">): Promise<JewelryItem> {
  const created = await apiFetch<ApiJewelryItem>("/api/items", {
    method: "POST",
    body: JSON.stringify({
      item_name: input.itemName,
      category: input.category,
      karat: input.karat,
      weight_grams: input.weightGrams,
      quantity: input.quantity,
      status: input.status,
      image_url: input.imageUrl,
    }),
  });
  window.dispatchEvent(new Event(CHANGED));
  return fromApi(created);
}

export async function deleteItem(id: string): Promise<void> {
  await apiFetch(`/api/items/${id}`, { method: "DELETE" });
  window.dispatchEvent(new Event(CHANGED));
}

export function useItems() {
  const [items, setItems] = useState<JewelryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const list = await apiFetch<ApiJewelryItem[]>("/api/items");
      setItems(list.map(fromApi));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load items");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const handler = () => refresh();
    window.addEventListener(CHANGED, handler);
    return () => window.removeEventListener(CHANGED, handler);
  }, [refresh]);

  return { items, loading, error, refresh };
}
