import { useState, useEffect, useCallback } from "react";
import { apiFetch } from "@/lib/api";

export interface ApiProduct {
  id: string;
  product_name: string;
  sku: string | null;
  category: string;
  karat: number;
  description: string | null;
  price: string | number | null;
  image_url: string | null;
  date_added: string;
}

export interface Product {
  id: string;
  productName: string;
  sku?: string;
  category: string;
  karat: number;
  description?: string;
  price?: number;
  imageUrl?: string;
  dateAdded: string;
}

function fromApi(p: ApiProduct): Product {
  return {
    id: p.id,
    productName: p.product_name,
    sku: p.sku || undefined,
    category: p.category,
    karat: Number(p.karat),
    description: p.description || undefined,
    price: p.price != null ? Number(p.price) : undefined,
    imageUrl: p.image_url || undefined,
    dateAdded: p.date_added,
  };
}

const CHANGED = "pvd_products_changed";

export interface ProductInput {
  productName: string;
  sku?: string;
  category: string;
  karat: number;
  description?: string;
  price?: number;
  imageUrl?: string;
}

function toApiBody(input: ProductInput) {
  return {
    product_name: input.productName,
    sku: input.sku,
    category: input.category,
    karat: input.karat,
    description: input.description,
    price: input.price,
    image_url: input.imageUrl,
  };
}

export async function createProduct(input: ProductInput): Promise<Product> {
  const created = await apiFetch<ApiProduct>("/api/products", {
    method: "POST",
    body: JSON.stringify(toApiBody(input)),
  });
  window.dispatchEvent(new Event(CHANGED));
  return fromApi(created);
}

export async function updateProduct(id: string, input: ProductInput): Promise<Product> {
  const updated = await apiFetch<ApiProduct>(`/api/products/${id}`, {
    method: "PUT",
    body: JSON.stringify(toApiBody(input)),
  });
  window.dispatchEvent(new Event(CHANGED));
  return fromApi(updated);
}

export async function deleteProduct(id: string): Promise<void> {
  await apiFetch(`/api/products/${id}`, { method: "DELETE" });
  window.dispatchEvent(new Event(CHANGED));
}

export function useProducts() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const list = await apiFetch<ApiProduct[]>("/api/products");
      setProducts(list.map(fromApi));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load products");
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

  return { products, loading, error, refresh };
}
