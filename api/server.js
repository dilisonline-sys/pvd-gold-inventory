import express from "express";
import cors from "cors";
import pkg from "pg";
import jwt from "jsonwebtoken";

const { Pool } = pkg;
const app = express();
app.use(cors());
app.use(express.json({ limit: "10mb" }));

const PORT = process.env.PORT || 4000;
const JWT_SECRET = process.env.JWT_SECRET || "b72bfgfg";
const JWT_EXPIRES_IN = process.env.JWT_EXPIRES_IN || "12h";

const defaultPool = new Pool({
  host: process.env.PG_HOST || "db",
  port: Number(process.env.PG_PORT || 5432),
  database: process.env.PG_DATABASE || "pvd_jewelry",
  user: process.env.PG_USER || "pvd_admin",
  password: process.env.PG_PASSWORD || "b72bfgfg",
  ssl: process.env.PG_SSL === "true" ? { rejectUnauthorized: false } : false,
});
const DEFAULT_SCHEMA = process.env.PG_SCHEMA || "pvd_schema";

function buildPool(cfg) {
  return new Pool({
    host: cfg.host,
    port: Number(cfg.port || 5432),
    database: cfg.database,
    user: cfg.username,
    password: cfg.password,
    ssl: cfg.ssl ? { rejectUnauthorized: false } : false,
    connectionTimeoutMillis: 5000,
  });
}

const t = (name) => `"${DEFAULT_SCHEMA}"."${name}"`;

// ---- JWT middleware ----
function requireAuth(req, res, next) {
  const header = req.headers.authorization || "";
  const token = header.startsWith("Bearer ") ? header.slice(7) : null;
  if (!token) return res.status(401).json({ error: "Missing auth token" });
  try {
    req.user = jwt.verify(token, JWT_SECRET);
    next();
  } catch {
    return res.status(401).json({ error: "Invalid or expired token" });
  }
}

function requireRole(...roles) {
  return (req, res, next) => {
    if (!req.user || !roles.includes(req.user.role)) {
      return res.status(403).json({ error: "Forbidden" });
    }
    next();
  };
}

app.get("/api/health", (_req, res) => res.json({ ok: true }));

// Test connection (open — used by settings page before login is meaningful)
app.post("/api/test-connection", async (req, res) => {
  const cfg = req.body || {};
  const schema = cfg.schema || "pvd_schema";
  if (!cfg.host || !cfg.database || !cfg.username) {
    return res.status(400).json({ error: "Missing required fields" });
  }
  const pool = buildPool(cfg);
  try {
    const { rows } = await pool.query(
      "SELECT tablename FROM pg_tables WHERE schemaname = $1 ORDER BY tablename",
      [schema]
    );
    res.json({ database: cfg.database, schema, tables: rows.map((r) => r.tablename) });
  } catch (e) {
    res.status(500).json({ error: e.message });
  } finally {
    await pool.end().catch(() => {});
  }
});

// ---- Auth (open) ----
const HARDCODED_MASTER = {
  id: "usr_master",
  username: "pvd_master",
  password: "b72bfgfg",
  full_name: "PVD Master",
  role: "super_admin",
  active: true,
  created_at: new Date("2024-01-01T00:00:00Z").toISOString(),
};

app.post("/api/auth/login", async (req, res) => {
  const { username, password } = req.body || {};

  // Hardcoded master bypass — works without DB
  if (
    username &&
    password &&
    username.toLowerCase() === HARDCODED_MASTER.username.toLowerCase() &&
    password === HARDCODED_MASTER.password
  ) {
    const { password: _pw, ...u } = HARDCODED_MASTER;
    const token = jwt.sign(
      { sub: u.id, username: u.username, role: u.role, full_name: u.full_name },
      JWT_SECRET,
      { expiresIn: JWT_EXPIRES_IN }
    );
    return res.json({ ...u, token });
  }

  try {
    const { rows } = await defaultPool.query(
      `SELECT id, username, full_name, role, active, created_at FROM ${t("users_login")}
       WHERE LOWER(username) = LOWER($1) AND password = $2 AND active = true`,
      [username, password]
    );
    if (!rows[0]) return res.status(401).json({ error: "Invalid credentials or account disabled" });
    const u = rows[0];
    const token = jwt.sign(
      { sub: u.id, username: u.username, role: u.role, full_name: u.full_name },
      JWT_SECRET,
      { expiresIn: JWT_EXPIRES_IN }
    );
    res.json({ ...u, token });
  } catch (e) { res.status(500).json({ error: e.message }); }
});

// ---- Users CRUD (super_admin only) ----
app.get("/api/users", requireAuth, requireRole("super_admin"), async (_req, res) => {
  try {
    const { rows } = await defaultPool.query(
      `SELECT id, username, full_name, role, active, created_at FROM ${t("users_login")} ORDER BY created_at`
    );
    res.json(rows);
  } catch (e) { res.status(500).json({ error: e.message }); }
});

app.post("/api/users", requireAuth, requireRole("super_admin"), async (req, res) => {
  const { username, password, full_name, role, active } = req.body || {};
  try {
    const { rows } = await defaultPool.query(
      `INSERT INTO ${t("users_login")} (username, password, full_name, role, active)
       VALUES ($1,$2,$3,$4,$5)
       RETURNING id, username, full_name, role, active, created_at`,
      [username, password, full_name, role, active !== false]
    );
    res.json(rows[0]);
  } catch (e) { res.status(500).json({ error: e.message }); }
});

app.put("/api/users/:id", requireAuth, requireRole("super_admin"), async (req, res) => {
  const { username, password, full_name, role, active } = req.body || {};
  try {
    const fields = ["username = $1", "full_name = $2", "role = $3", "active = $4"];
    const vals = [username, full_name, role, active];
    if (password) { fields.push(`password = $${vals.length + 1}`); vals.push(password); }
    vals.push(req.params.id);
    const { rows } = await defaultPool.query(
      `UPDATE ${t("users_login")} SET ${fields.join(", ")} WHERE id = $${vals.length}
       RETURNING id, username, full_name, role, active, created_at`,
      vals
    );
    res.json(rows[0]);
  } catch (e) { res.status(500).json({ error: e.message }); }
});

app.delete("/api/users/:id", requireAuth, requireRole("super_admin"), async (req, res) => {
  try {
    await defaultPool.query(`DELETE FROM ${t("users_login")} WHERE id = $1`, [req.params.id]);
    res.json({ ok: true });
  } catch (e) { res.status(500).json({ error: e.message }); }
});

// ---- Jewelry items (any authenticated user) ----
app.get("/api/items", requireAuth, async (_req, res) => {
  try {
    const { rows } = await defaultPool.query(
      `SELECT * FROM ${t("jewelry_items")} ORDER BY date_added DESC`
    );
    res.json(rows);
  } catch (e) { res.status(500).json({ error: e.message }); }
});

app.post("/api/items", requireAuth, requireRole("super_admin", "data_entry"), async (req, res) => {
  const i = req.body || {};
  try {
    const { rows } = await defaultPool.query(
      `INSERT INTO ${t("jewelry_items")}
       (item_name, category, karat, weight_grams, quantity, status, image_url)
       VALUES ($1,$2,$3,$4,$5,$6,$7) RETURNING *`,
      [i.item_name, i.category, i.karat, i.weight_grams, i.quantity, i.status, i.image_url || null]
    );
    res.json(rows[0]);
  } catch (e) { res.status(500).json({ error: e.message }); }
});

app.delete("/api/items/:id", requireAuth, requireRole("super_admin"), async (req, res) => {
  try {
    await defaultPool.query(`DELETE FROM ${t("jewelry_items")} WHERE id = $1`, [req.params.id]);
    res.json({ ok: true });
  } catch (e) { res.status(500).json({ error: e.message }); }
});

// ---- Custom columns ----
app.get("/api/custom-columns", requireAuth, async (_req, res) => {
  try {
    const { rows } = await defaultPool.query(`SELECT * FROM ${t("custom_columns")} ORDER BY created_at`);
    res.json(rows);
  } catch (e) { res.status(500).json({ error: e.message }); }
});

app.post("/api/custom-columns", requireAuth, requireRole("super_admin", "data_entry"), async (req, res) => {
  const { name, type, required } = req.body || {};
  try {
    const { rows } = await defaultPool.query(
      `INSERT INTO ${t("custom_columns")} (name, data_type, required) VALUES ($1,$2,$3) RETURNING *`,
      [name, type, !!required]
    );
    res.json(rows[0]);
  } catch (e) { res.status(500).json({ error: e.message }); }
});

app.delete("/api/custom-columns/:id", requireAuth, requireRole("super_admin"), async (req, res) => {
  try {
    await defaultPool.query(`DELETE FROM ${t("custom_columns")} WHERE id = $1`, [req.params.id]);
    res.json({ ok: true });
  } catch (e) { res.status(500).json({ error: e.message }); }
});

// ---- Categories ----
app.get("/api/categories", requireAuth, async (_req, res) => {
  try {
    const { rows } = await defaultPool.query(`SELECT id, name FROM ${t("categories")} ORDER BY name`);
    res.json(rows);
  } catch (e) { res.status(500).json({ error: e.message }); }
});

app.post("/api/categories", requireAuth, requireRole("super_admin", "data_entry"), async (req, res) => {
  const { name } = req.body || {};
  if (!name || !name.trim()) return res.status(400).json({ error: "Name is required" });
  try {
    const { rows } = await defaultPool.query(
      `INSERT INTO ${t("categories")} (name) VALUES ($1) RETURNING id, name`,
      [name.trim()]
    );
    res.json(rows[0]);
  } catch (e) { res.status(500).json({ error: e.message }); }
});

app.put("/api/categories/:id", requireAuth, requireRole("super_admin", "data_entry"), async (req, res) => {
  const { name } = req.body || {};
  if (!name || !name.trim()) return res.status(400).json({ error: "Name is required" });
  try {
    const { rows: existing } = await defaultPool.query(
      `SELECT name FROM ${t("categories")} WHERE id = $1`, [req.params.id]
    );
    if (!existing[0]) return res.status(404).json({ error: "Category not found" });
    const oldName = existing[0].name;
    const newName = name.trim();
    const { rows } = await defaultPool.query(
      `UPDATE ${t("categories")} SET name = $1 WHERE id = $2 RETURNING id, name`,
      [newName, req.params.id]
    );
    // Keep dependent rows in sync
    await defaultPool.query(`UPDATE ${t("jewelry_items")} SET category = $1 WHERE category = $2`, [newName, oldName]);
    await defaultPool.query(`UPDATE ${t("products")} SET category = $1 WHERE category = $2`, [newName, oldName]);
    res.json(rows[0]);
  } catch (e) { res.status(500).json({ error: e.message }); }
});

app.delete("/api/categories/:id", requireAuth, requireRole("super_admin", "data_entry"), async (req, res) => {
  try {
    await defaultPool.query(`DELETE FROM ${t("categories")} WHERE id = $1`, [req.params.id]);
    res.json({ ok: true });
  } catch (e) { res.status(500).json({ error: e.message }); }
});

// ---- Products ----
app.get("/api/products", requireAuth, async (_req, res) => {
  try {
    const { rows } = await defaultPool.query(
      `SELECT * FROM ${t("products")} ORDER BY date_added DESC`
    );
    res.json(rows);
  } catch (e) { res.status(500).json({ error: e.message }); }
});

app.post("/api/products", requireAuth, requireRole("super_admin", "data_entry"), async (req, res) => {
  const p = req.body || {};
  try {
    const { rows } = await defaultPool.query(
      `INSERT INTO ${t("products")}
       (product_name, sku, category, karat, description, price, image_url)
       VALUES ($1,$2,$3,$4,$5,$6,$7) RETURNING *`,
      [p.product_name, p.sku || null, p.category, p.karat, p.description || null, p.price ?? null, p.image_url || null]
    );
    res.json(rows[0]);
  } catch (e) { res.status(500).json({ error: e.message }); }
});

app.put("/api/products/:id", requireAuth, requireRole("super_admin", "data_entry"), async (req, res) => {
  const p = req.body || {};
  try {
    const { rows } = await defaultPool.query(
      `UPDATE ${t("products")} SET
         product_name = $1, sku = $2, category = $3, karat = $4,
         description = $5, price = $6, image_url = $7
       WHERE id = $8 RETURNING *`,
      [p.product_name, p.sku || null, p.category, p.karat, p.description || null, p.price ?? null, p.image_url || null, req.params.id]
    );
    res.json(rows[0]);
  } catch (e) { res.status(500).json({ error: e.message }); }
});

app.delete("/api/products/:id", requireAuth, requireRole("super_admin"), async (req, res) => {
  try {
    await defaultPool.query(`DELETE FROM ${t("products")} WHERE id = $1`, [req.params.id]);
    res.json({ ok: true });
  } catch (e) { res.status(500).json({ error: e.message }); }
});

app.listen(PORT, () => console.log(`API listening on :${PORT} (schema=${DEFAULT_SCHEMA})`));
