## Why This Exists

A **minimal CMS API for local businesses** — built as a free/low-cost solution for shops, churches, and cafes to manage their content without paying for enterprise tools.

Target: ~10–20 local clients. Not built to scale to SaaS levels, and that's intentional.

---

## Tech Stack (All Free Tier)

| Layer | Tool |
|---|---|
| Backend | Python 3.12, FastAPI (async) |
| Auth | Supabase Auth |
| Database | PostgreSQL via Supabase |
| File Storage | Supabase Storage |
| Cache / Rate Limiting | Upstash Redis |
| Hosting | Heroku  |
| Migrations | Alembic |

---

## Architecture

Layered architecture: **Router → Service → Repository → Database**

- `BaseRepository[T]` — generic CRUD, slug generation
- `TenantScopeRepository[T]` — all queries scoped to `tenant_id`
- `PublishableMixin` — optional `is_published` filtering
- `SoftDeleteMixin` — optional soft delete support
- Custom exception hierarchy maps cleanly to HTTP status codes
- Structured logging throughout (`structlog`)

### Multi-Tenancy Design
Shared schema, row-level isolation. Every tenant-scoped table carries a `tenant_id` foreign key. All queries are filtered at the repository layer — services cannot accidentally bypass tenant scoping.

Staff accounts use synthetic emails: `{username}@{tenant.slug}.keta.com`

---

## Features

| Feature | Description |
|---|---|
| **Auth** | Sign up, sign in via Supabase. JWT verification on protected routes. |
| **Tenants** | Create and manage client tenants. Developer-managed setup. |
| **Tenant Members** | Staff accounts scoped to a tenant with role support (owner/member). |
| **Gallery** | Albums with cover images. Bulk image upload to Supabase Storage. |
| **Content Types** | Define custom content schemas with JSON Schema validation. |
| **Content Entries** | Create and manage entries validated against their content type schema. |

### Use Cases
- Church event calendars + photo galleries
- Restaurant menus
- Small business portfolios

---

## Getting Started

### Prerequisites
- Python 3.12+
- Docker & Docker Compose
- Supabase project (free tier)
- Upstash Redis account (free tier)

### Setup

```bash
git clone https://github.com/MarvinPescos/minimal-cms-core.git
cd minimal-cms-core/backend

# Copy environment template and fill in credentials
cp .env.example .env

# Run with Docker
docker-compose up -d

# Run migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload
```

### Environment Variables

See `.env.example` for the full list. Required:
- `DB_URL` — PostgreSQL async connection string
- `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`
- `REDIS_URL` — Upstash Redis URL (`rediss://...`)

---

## Tenant Setup

**Developer (admin):**
1. `POST /tenants` — create the tenant (slug auto-generated from name)
2. `POST /tenant/members` — create the owner account for that tenant
3. Hand off owner credentials to the client

**Owner (once authenticated):**
- `POST /tenant/members` — create and manage their own staff accounts

---

## API Docs

Available at `/docs` (Swagger UI) when the server is running.