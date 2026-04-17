import { useState, useEffect, useCallback } from "react";
import { apiFetch } from "@/lib/api";

export interface CustomColumn {
  id: string;
  name: string;
  type: "TEXT" | "NUMBER" | "DATE" | "BLOB";
  required: boolean;
}

interface ApiCustomColumn {
  id: string;
  name: string;
  data_type: string;
  required: boolean;
}

function fromApi(c: ApiCustomColumn): CustomColumn {
  return { id: c.id, name: c.name, type: c.data_type as CustomColumn["type"], required: c.required };
}

const CHANGED = "pvd_columns_changed";

export async function addCustomColumn(col: Omit<CustomColumn, "id">): Promise<CustomColumn> {
  const created = await apiFetch<ApiCustomColumn>("/api/custom-columns", {
    method: "POST",
    body: JSON.stringify({ name: col.name, type: col.type, required: col.required }),
  });
  window.dispatchEvent(new Event(CHANGED));
  return fromApi(created);
}

export async function removeCustomColumn(id: string): Promise<void> {
  await apiFetch(`/api/custom-columns/${id}`, { method: "DELETE" });
  window.dispatchEvent(new Event(CHANGED));
}

export function useCustomColumns() {
  const [columns, setColumns] = useState<CustomColumn[]>([]);

  const refresh = useCallback(async () => {
    try {
      const list = await apiFetch<ApiCustomColumn[]>("/api/custom-columns");
      setColumns(list.map(fromApi));
    } catch {
      setColumns([]);
    }
  }, []);

  useEffect(() => {
    refresh();
    const handler = () => refresh();
    window.addEventListener(CHANGED, handler);
    return () => window.removeEventListener(CHANGED, handler);
  }, [refresh]);

  return columns;
}
