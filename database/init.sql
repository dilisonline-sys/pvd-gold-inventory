-- =====================================================
-- PVD Gold Jewelry Inventory - Database Init Script
-- =====================================================
-- This script runs automatically when PostgreSQL starts
-- for the first time. Place in /docker-entrypoint-initdb.d/
-- -----------------------------------------------------

-- 0. Create Schema
CREATE SCHEMA IF NOT EXISTS pvd_schema;
SET search_path TO pvd_schema;

-- 1. Users Table (for authentication)
CREATE TABLE IF NOT EXISTS pvd_schema.users_login (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('super_admin', 'data_entry', 'inventory')),
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_username ON pvd_schema.users_login(username);
CREATE INDEX IF NOT EXISTS idx_users_role ON pvd_schema.users_login(role);

-- 2. Categories Table (managed list shared by inventory + products)
CREATE TABLE IF NOT EXISTS pvd_schema.categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO pvd_schema.categories (name) VALUES
    ('Chains'), ('Bracelets'), ('Rings'), ('Earrings'),
    ('Pendants'), ('Necklaces'), ('Bangles')
ON CONFLICT (name) DO NOTHING;

-- 3. Jewelry Items Table (main inventory)
CREATE TABLE IF NOT EXISTS pvd_schema.jewelry_items (
    id VARCHAR(20) PRIMARY KEY,
    item_name VARCHAR(200) NOT NULL,
    category VARCHAR(50) NOT NULL,
    karat INTEGER NOT NULL CHECK (karat IN (10, 14, 18, 22, 24)),
    weight_grams DECIMAL(10, 2) NOT NULL CHECK (weight_grams > 0),
    quantity INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    date_added DATE NOT NULL DEFAULT CURRENT_DATE,
    status VARCHAR(20) NOT NULL CHECK (status IN ('In Stock', 'Sold', 'On Display', 'Reserved')),
    image_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_items_category ON pvd_schema.jewelry_items(category);
CREATE INDEX IF NOT EXISTS idx_items_status ON pvd_schema.jewelry_items(status);
CREATE INDEX IF NOT EXISTS idx_items_karat ON pvd_schema.jewelry_items(karat);
CREATE INDEX IF NOT EXISTS idx_items_date_added ON pvd_schema.jewelry_items(date_added);

-- 4. Products Table (catalog / SKUs, separate from inventory)
CREATE TABLE IF NOT EXISTS pvd_schema.products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_name VARCHAR(200) NOT NULL,
    sku VARCHAR(50) UNIQUE,
    category VARCHAR(50) NOT NULL,
    karat INTEGER NOT NULL CHECK (karat IN (10, 14, 18, 22, 24)),
    description TEXT,
    price DECIMAL(12, 2),
    image_url TEXT,
    date_added DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_products_category ON pvd_schema.products(category);
CREATE INDEX IF NOT EXISTS idx_products_karat ON pvd_schema.products(karat);

-- 5. Custom Columns Definition Table
CREATE TABLE IF NOT EXISTS pvd_schema.custom_columns (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(10) NOT NULL CHECK (type IN ('TEXT', 'NUMBER', 'DATE', 'BLOB')),
    required BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 6. Item Custom Values Table
CREATE TABLE IF NOT EXISTS pvd_schema.item_custom_values (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    item_id VARCHAR(20) NOT NULL REFERENCES pvd_schema.jewelry_items(id) ON DELETE CASCADE,
    column_id VARCHAR(50) NOT NULL REFERENCES pvd_schema.custom_columns(id) ON DELETE CASCADE,
    value_text TEXT,
    value_number DECIMAL(15, 2),
    value_date DATE,
    value_blob BYTEA,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(item_id, column_id)
);

CREATE INDEX IF NOT EXISTS idx_custom_values_item ON pvd_schema.item_custom_values(item_id);

-- 7. Trigger function for auto-updating timestamps
CREATE OR REPLACE FUNCTION pvd_schema.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_users_updated_at ON pvd_schema.users_login;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON pvd_schema.users_login
    FOR EACH ROW EXECUTE FUNCTION pvd_schema.update_updated_at_column();

DROP TRIGGER IF EXISTS update_items_updated_at ON pvd_schema.jewelry_items;
CREATE TRIGGER update_items_updated_at
    BEFORE UPDATE ON pvd_schema.jewelry_items
    FOR EACH ROW EXECUTE FUNCTION pvd_schema.update_updated_at_column();

DROP TRIGGER IF EXISTS update_products_updated_at ON pvd_schema.products;
CREATE TRIGGER update_products_updated_at
    BEFORE UPDATE ON pvd_schema.products
    FOR EACH ROW EXECUTE FUNCTION pvd_schema.update_updated_at_column();

DROP TRIGGER IF EXISTS update_categories_updated_at ON pvd_schema.categories;
CREATE TRIGGER update_categories_updated_at
    BEFORE UPDATE ON pvd_schema.categories
    FOR EACH ROW EXECUTE FUNCTION pvd_schema.update_updated_at_column();

DROP TRIGGER IF EXISTS update_custom_values_updated_at ON pvd_schema.item_custom_values;
CREATE TRIGGER update_custom_values_updated_at
    BEFORE UPDATE ON pvd_schema.item_custom_values
    FOR EACH ROW EXECUTE FUNCTION pvd_schema.update_updated_at_column();

-- 8. Insert Default Super Admin (only if not exists)
INSERT INTO pvd_schema.users_login (id, username, password, full_name, role, active)
VALUES (
    'usr_master',
    'pvd_master',
    'b72bfgfg',
    'PVD Master Admin',
    'super_admin',
    true
)
ON CONFLICT (id) DO NOTHING;
