import { useState, useEffect, useCallback } from "react";

export interface CustomColumn {
  id: string;
  name: string;
  type: "TEXT" | "NUMBER" | "DATE" | "BLOB";
  required: boolean;
}

const STORAGE_KEY = "pvd_custom_columns";

function loadColumns(): CustomColumn[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveColumns(cols: CustomColumn[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(cols));
  window.dispatchEvent(new Event("pvd_columns_changed"));
}

export function addCustomColumn(col: Omit<CustomColumn, "id">): CustomColumn {
  const columns = loadColumns();
  const newCol: CustomColumn = { ...col, id: `custom_${Date.now()}` };
  columns.push(newCol);
  saveColumns(columns);
  return newCol;
}

export function removeCustomColumn(id: string) {
  const columns = loadColumns().filter((c) => c.id !== id);
  saveColumns(columns);
}

export function useCustomColumns() {
  const [columns, setColumns] = useState<CustomColumn[]>(loadColumns);

  const refresh = useCallback(() => {
    setColumns(loadColumns());
  }, []);

  useEffect(() => {
    window.addEventListener("pvd_columns_changed", refresh);
    return () => window.removeEventListener("pvd_columns_changed", refresh);
  }, [refresh]);

  return columns;
}
