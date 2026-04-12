export interface JewelryItem {
  id: string;
  itemName: string;
  category: string;
  karat: number;
  weightGrams: number;
  quantity: number;
  dateAdded: string;
  status: "In Stock" | "Sold" | "On Display" | "Reserved";
  imageUrl?: string;
  customFields?: Record<string, string>;
}

export const mockInventory: JewelryItem[] = [
  {
    id: "PVD-001",
    itemName: "Cuban Link Chain 22\"",
    category: "Chains",
    karat: 18,
    weightGrams: 45.2,
    quantity: 3,
    dateAdded: "2026-03-15",
    status: "In Stock",
    imageUrl: "https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f?w=100&h=100&fit=crop",
  },
  {
    id: "PVD-002",
    itemName: "Diamond Tennis Bracelet",
    category: "Bracelets",
    karat: 14,
    weightGrams: 12.8,
    quantity: 2,
    dateAdded: "2026-03-20",
    status: "On Display",
    imageUrl: "https://images.unsplash.com/photo-1611591437281-460bfbe1220a?w=100&h=100&fit=crop",
  },
  {
    id: "PVD-003",
    itemName: "Signet Ring - Eagle",
    category: "Rings",
    karat: 24,
    weightGrams: 8.5,
    quantity: 5,
    dateAdded: "2026-04-01",
    status: "In Stock",
    imageUrl: "https://images.unsplash.com/photo-1605100804763-247f67b3557e?w=100&h=100&fit=crop",
  },
  {
    id: "PVD-004",
    itemName: "Rope Chain 24\"",
    category: "Chains",
    karat: 22,
    weightGrams: 38.0,
    quantity: 1,
    dateAdded: "2026-04-05",
    status: "Reserved",
    imageUrl: "https://images.unsplash.com/photo-1599643477877-530eb83abc8e?w=100&h=100&fit=crop",
  },
  {
    id: "PVD-005",
    itemName: "Hoop Earrings - Large",
    category: "Earrings",
    karat: 18,
    weightGrams: 6.2,
    quantity: 8,
    dateAdded: "2026-04-08",
    status: "In Stock",
    imageUrl: "https://images.unsplash.com/photo-1630019852942-f89202989a59?w=100&h=100&fit=crop",
  },
  {
    id: "PVD-006",
    itemName: "Pendant - Lion Head",
    category: "Pendants",
    karat: 14,
    weightGrams: 15.3,
    quantity: 0,
    dateAdded: "2026-02-10",
    status: "Sold",
  },
];

export const categories = ["Chains", "Bracelets", "Rings", "Earrings", "Pendants", "Necklaces", "Bangles"];
export const karatOptions = [10, 14, 18, 22, 24];
export const statusOptions: JewelryItem["status"][] = ["In Stock", "Sold", "On Display", "Reserved"];
