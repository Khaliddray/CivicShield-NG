# CIVICSHIELD NG — PRODUCTION DEPLOYMENT GUIDE

**Target Environment:** Linux Container Host (Docker / Kubernetes)  
**Database:** Managed PostgreSQL 16+ with SSL enforce  
**Cache / Message Queue:** Redis 7+  
**Web Server / Proxy:** Nginx with Let's Encrypt TLS

---

## 1. Production Architecture Overview

```
[ Internet Traffic ]
        |
        v
[ Cloudflare / Edge CDN ] (DDoS mitigation & SSL termination)
        |
        v
[ Nginx Reverse Proxy ] (Port 80/443 -> Gzip, Rate Limiting, Header Hardening)
        |
        +---> /api/v1/* ----------> [ FastAPI Backend Cluster ] (Port 8000)
        |                           (Uvicorn workers managed by Gunicorn)
        |
        +---> /* (Static Assets) --> [ React SPA Dist ] (Vite Built Bundle)
                                            |
                         +------------------+------------------+
                         |                                     |
                         v                                     v
                [ PostgreSQL 16+ ]                         [ Redis 7+ ]
               (Relational Persistence)            (Background Dispatch / Lockout)
```

---

## 2. Environment Variables Checklist

Create a secure `.env` file based on `.env.example`:

| Variable | Recommended Production Value | Description |
|---|---|---|
| `ENVIRONMENT` | `production` | Enables strict production settings & disables debug logs |
| `SECRET_KEY` | 64-character random hex string | Signs JWT tokens (`openssl rand -hex 32`) |
| `DATABASE_URL` | `postgresql+psycopg2://user:pass@host:5432/civicshield` | PostgreSQL connection string |
| `DATABASE_POOL_SIZE` | `20` | Database connection pool size |
| `DATABASE_MAX_OVERFLOW` | `10` | Max overflow connections beyond pool size |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | JWT access token validity |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | JWT refresh token validity |
| `CORS_ORIGINS` | `["https://civicshield.ng", "https://command.civicshield.ng"]` | Allowed web origins |
| `UPLOAD_DIR` | `/app/uploads` | Absolute path for encrypted media storage |

---

## 3. Database Migration Execution

Apply schema migrations safely in your deployment pipeline:

```bash
# 1. Run Alembic migrations against target database
alembic upgrade head

# 2. Seed RBAC roles and permissions (idempotent operation)
python3 -c "from backend.app.core.init_db import init_database; init_database()"
```

---

## 4. Container Deployment via Docker Compose

Run the production multi-container stack:

```bash
# Build and start services in detached mode
docker compose -f docker-compose.yml up -d --build

# Inspect service health status
docker compose ps

# Tail backend service logs
docker compose logs -f backend
```

---

## 5. Security & Operational Hardening

1. **Non-Root Execution:** All Docker containers run as an unprivileged user (`civicshield:civicshield`, UID/GID 10001).
2. **Container Security Flags:** Mount root filesystem as read-only (`read_only: true`), dropping all unnecessary Linux capabilities (`cap_drop: ["ALL"]`).
3. **Database Security:** Enforce least-privilege database user. Never use superuser `postgres` for application connections.
4. **Regular Backup:** Automated daily pg_dump cron with cryptographic verification of database backups.
