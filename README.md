# PVD Goldsmith Manufacturing System

**Version: v1.5**

A complete web-based manufacturing management system for goldsmith jewelry companies. Tracks every step of the jewelry production process — from customer order and design through casting, polishing, stone setting, quality control, and final delivery.

---

## Features

- **11-Stage Manufacturing Pipeline** — each stage is linked to the next: Design → Wax Carving → Investment/Burnout → Casting → Filing → Polishing → Stone Setting → QC → Plating → Final Inspection → Packaging
- **Job Order Management** — create and track customer orders with metal type, purity, stone specifications, and cost tracking
- **Inventory Management** — raw material stock tracking with low-stock alerts, bulk CSV upload, and full transaction history
- **Weight Tracking** — gold weight in/out recorded at every production stage; waste and loss reports generated automatically
- **Quality Control** — QC checks per stage with pass/fail/conditional grades and corrective action tracking
- **Role-Based Access Control** — 6 user levels with enforced permissions
- **Reports** — production stats, inventory levels, gold consumption, order revenue, worker productivity
- **Kanban Stage Board** — live view of all jobs by current production stage

---

## User Roles

| Role | Permissions |
|------|------------|
| **Administrator** | Full access — user management, all features |
| **Manager** | All features + reports; cannot manage users |
| **Supervisor** | Create/manage jobs and orders, all stage operations |
| **Production Worker** | View jobs; update stages assigned to them |
| **Inventory Clerk** | Stock entry, bulk upload, material management |
| **Viewer** | Read-only access across all modules |

---

## Quick Start — Docker (Recommended)

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/) installed

### 1. Clone the repository

```bash
git clone https://github.com/dilisonline-sys/pvd-gold-inventory.git
cd pvd-gold-inventory
```

> If running from the feature branch:
> ```bash
> git checkout claude/affectionate-newton-03hpL
> ```

### 2. Build and start the container

```bash
docker compose up --build
```

The first run automatically:
- Runs all database migrations
- Creates 11 manufacturing process stages
- Populates material categories and jewelry item types
- Creates demo user accounts
- Collects static files

### 3. Access the app

Open your browser and go to:

```
http://localhost:8000
```

### 4. Log in

| Username | Password | Role |
|----------|----------|------|
| `admin` | `admin123` | Administrator |
| `manager` | `manager123` | Manager |
| `supervisor` | `super123` | Supervisor |
| `worker` | `worker123` | Production Worker |
| `inventory` | `inv123` | Inventory Clerk |

> **Tip:** Log in as `admin` first to create your real user accounts, then deactivate the demo users.

### 5. Stop the app

```bash
docker compose down
```

Data is stored in named Docker volumes (`db_data`, `media_data`) and persists between restarts. To reset everything:

```bash
docker compose down -v   # removes volumes too
```

### Updating to a new version

```bash
git pull
docker compose down
docker compose up --build
```

> Always use `--build` after a `git pull` so Docker rebuilds the image with the latest code.

---

## Manual Installation (Without Docker)

### Prerequisites
- Python 3.11+
- pip

### 1. Clone and enter the project

```bash
git clone https://github.com/dilisonline-sys/pvd-gold-inventory.git
cd pvd-gold-inventory
git checkout claude/affectionate-newton-03hpL
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run migrations

```bash
python manage.py migrate
```

### 5. Load initial data and demo users

```bash
python manage.py setup_initial_data
```

Output will confirm stages, categories, and users created.

### 6. Start the development server

```bash
python manage.py runserver
```

### 7. Open the app

```
http://127.0.0.1:8000
```

Log in with `admin` / `admin123`.

---

## Bulk Stock Entry (CSV Upload)

Inventory clerks and above can upload stock in bulk via **Inventory → Bulk Stock Upload**.

CSV format:

```
material_name,quantity,unit_cost,supplier_name,batch_number,purity,notes
Gold 18K,100.5,85.00,Gold Suppliers Ltd,BATCH-001,18K,18 karat alloy
Silver 925,500.0,1.20,Silver Imports Co,BATCH-002,925,Sterling silver
Diamond Round 1ct,25,500.00,Gem House,GEM-001,,Round brilliant cut
```

A sample CSV can be downloaded directly from the Bulk Stock Upload page.

---

## Project Structure

```
pvd-gold-inventory/
├── accounts/          # Custom user model, roles, login/auth
├── inventory/         # Stock management, materials, suppliers
├── manufacturing/     # 11-stage production pipeline, QC, weight tracking
├── orders/            # Customer job orders
├── reports/           # Management reports
├── templates/         # HTML templates (Bootstrap 5)
├── static/            # CSS, JS, sample files
├── Dockerfile
├── docker-compose.yml
├── entrypoint.sh
└── manage.py
```

---

## Tech Stack

- **Backend:** Django 5.2 (Python 3.11)
- **Database:** SQLite (file-based, zero config)
- **Frontend:** Bootstrap 5, Bootstrap Icons
- **Container:** Docker + Docker Compose

---

## License

Internal use — PVD Goldsmith Manufacturing Company.
