## Why This Exists

Built this as a **free/low-cost CMS API for local businesses** in your area. 

A **minimal CMS API for local businesses** in your area. Built to provide zero to minimal cost solutions for shops/churches/cafes to manage contents system.

### **Tech Stack (All Free Tier):**
- Backend: Python (FastAPI)
- Supabase: Auth, PostgreSQL, Storage (Free Tier / Paid)
- Upstash: Redis (Free Tier / Paid)
- Heroku: Hosting (GitHub Student Pack)

### **Design Decision: Table-Level Multi-Tenancy**
- Target: ~10-20 local clients max
- Complete data isolation per client
- Trade-off: Doesn't scale to SaaS levels (and that's fine)

### Use Cases
- Church event calendars + photo galleries
- Restaurant menus (add feature if needed only gallery and event are provided.)
- Small business portfolios

---

## Getting Started

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Supabase account (free tier)
- Upstash Redis account (free tier, for production)

### Setup

```bash
# Clone the repo
git clone https://github.com/MarvinPescos/minimal-cms-core.git
cd minimal-cms/backend

# Copy environment template
cp .env.example .env
# Edit .env with your Supabase/Redis credentials

# Run with Docker
docker-compose up -d

# Run migrations
alembic upgrade head
```

### Access
- API: http://localhost:8001
- Swagger Docs: http://localhost:8001/docs

---

## Tenant Setup
This is developer-managed. To add a client:
1. Run migrations for their tables
2. Create admin via `/auth/signup`
3. Hand off credentials

---

**Note:** This is production code serving real businesses, not a tutorial project.