import express from "express";
import cors from "cors";
import pkg from "pg";

const { Pool } = pkg;
const app = express();
app.use(cors());
app.use(express.json());

const PORT = process.env.PORT || 4000;

// Default pool from env (used by /api/* routes that don't pass overrides)
const defaultPool = new Pool({
  host: process.env.PG_HOST || "db",
  port: Number(process.env.PG_PORT || 5432),
  database: process.env.PG_DATABASE || "pvd_jewelry",
  user: process.env.PG_USER || "pvd_admin",
  password: process.env.PG_PASSWORD || "changeme_in_production",
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

app.get("/api/health", (_req, res) => res.json({ ok: true }));

// Test connection — accepts a config in body, opens a temp pool, lists tables in schema
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
    res.json({
      database: cfg.database,
      schema,
      tables: rows.map((r) => r.tablename),
    });
  } catch (e) {
    res.status(500).json({ error: e.message });
  } finally {
    await pool.end().catch(() => {});
  }
});

// Helper to qualify table names with the active schema
const t = (name) => `"${DEFAULT_SCHEMA}"."${name}"`;

// ----- Users -----
app.get("/api/users", async (_req, res) => {
  try {
    const { rows } = await defaultPool.query(
      `SELECT id, username, full_name, role, active, created_at FROM ${t("users_login")} ORDER BY created_at`
    );
    res.json(rows);
  } catch (e) { res.status(500).json({ error: e.message }); }
});

app.post("/api/auth/login", async (req, res) => {
  const { username, password } = req.body || {};
  try {
    const { rows } = await defaultPool.query(
      `SELECT id, username, full_name, role, active FROM ${t("users_login")}
       WHERE LOWER(username) = LOWER($1) AND password_hash = $2 AND active = true`,
      [username, password]
    );
    if (!rows[0]) return res.status(401).json({ error: "Invalid credentials" });
    res.json(rows[0]);
  } catch (e) { res.status(500).json({ error: e.message }); }
});

// ----- Jewelry items -----
app.get("/api/items", async (_req, res) => {
  try {
    const { rows } = await defaultPool.query(
      `SELECT * FROM ${t("jewelry_items")} ORDER BY date_added DESC`
    );
    res.json(rows);
  } catch (e) { res.status(500).json({ error: e.message }); }
});

app.post("/api/items", async (req, res) => {
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

// ----- Custom columns -----
app.get("/api/custom-columns", async (_req, res) => {
  try {
    const { rows } = await defaultPool.query(`SELECT * FROM ${t("custom_columns")} ORDER BY created_at`);
    res.json(rows);
  } catch (e) { res.status(500).json({ error: e.message }); }
});

app.post("/api/custom-columns", async (req, res) => {
  const { name, type, required } = req.body || {};
  try {
    const { rows } = await defaultPool.query(
      `INSERT INTO ${t("custom_columns")} (name, data_type, required) VALUES ($1,$2,$3) RETURNING *`,
      [name, type, !!required]
    );
    res.json(rows[0]);
  } catch (e) { res.status(500).json({ error: e.message }); }
});

app.delete("/api/custom-columns/:id", async (req, res) => {
  try {
    await defaultPool.query(`DELETE FROM ${t("custom_columns")} WHERE id = $1`, [req.params.id]);
    res.json({ ok: true });
  } catch (e) { res.status(500).json({ error: e.message }); }
});

app.listen(PORT, () => console.log(`API listening on :${PORT} (schema=${DEFAULT_SCHEMA})`));
