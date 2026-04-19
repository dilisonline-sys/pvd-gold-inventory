import { useState, useEffect, useCallback } from "react";
import { apiFetch } from "@/lib/api";

export interface Category {
  id: string;
  name: string;
}

const CHANGED = "pvd_categories_changed";

function notify() {
  window.dispatchEvent(new Event(CHANGED));
}

export async function addCategory(name: string): Promise<Category> {
  const c = await apiFetch<Category>("/api/categories", {
    method: "POST",
    body: JSON.stringify({ name }),
  });
  notify();
  return c;
}

export async function updateCategory(id: string, name: string): Promise<Category> {
  const c = await apiFetch<Category>(`/api/categories/${id}`, {
    method: "PUT",
    body: JSON.stringify({ name }),
  });
  notify();
  // Items/products were renamed server-side; refresh those views too.
  window.dispatchEvent(new Event("pvd_items_changed"));
  window.dispatchEvent(new Event("pvd_products_changed"));
  return c;
}

export async function deleteCategory(id: string): Promise<void> {
  await apiFetch(`/api/categories/${id}`, { method: "DELETE" });
  notify();
}

export function useCategories() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const list = await apiFetch<Category[]>("/api/categories");
      setCategories(list);
    } catch {
      setCategories([]);
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

  return { categories, loading, refresh };
}
