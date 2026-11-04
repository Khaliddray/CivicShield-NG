# CIVICSHIELD NG — LOCAL DEVELOPMENT GUIDE

**Development Environment:** Linux, macOS, or Windows WSL2  
**Python Runtime:** Python 3.12+  
**Node.js Runtime:** Node.js 18+ & npm 10+

---

## 1. Prerequisites & Workspace Setup

Clone the repository and enter the project root:

```bash
git clone https://github.com/CivicShield-NG/CivicShield-NG.git
cd CivicShield-NG
```

---

## 2. Running the Backend

The backend utilizes SQLite with Write-Ahead Logging (WAL) and foreign keys enabled out-of-the-box for local development.

```bash
# 1. Run database initialization and RBAC seed
python3 -c "from backend.app.core.init_db import init_database; init_database()"

# 2. Start FastAPI development server with auto-reload
python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

The interactive OpenAPI documentation will be accessible at:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

---

## 3. Running the Frontend

The frontend is built with React 18, TypeScript, Tailwind CSS, and Vite.

```bash
# 1. Enter frontend folder and install dependencies
cd frontend
npm install

# 2. Launch Vite development server with backend proxy
npm run dev
```

The web application will open at:
- `http://localhost:5173`

Requests to `/api/*` are automatically proxied to `http://localhost:8000`.

---

## 4. Running the Test Suite

The test suite exercises all 50 backend unit and integration tests across all modules:

```bash
# Run full unified test runner
python3 run_tests.py
```

Test suite coverage:
- **`test_ai_engine.py`**: Prompt defense, categorization, contradiction detection.
- **`test_auth.py`**: Argon2id hashing, lockout, JWT claims, RBAC guards.
- **`test_database.py`**: Schema constraints, foreign key cascades, migrations.
- **`test_reporting.py`**: Report creation, IP privacy hashing, media validation.
- **`test_registry.py`**: Canonical SHA-256 hash checks, tampering alerts.
- **`test_notifications.py`**: Dual-key approvals, duplicate suppression, state feeds.
- **`test_narratives.py`**: Cluster grouping, propagation velocity, threat graph.
- **`test_security.py`**: Tamper-evident hash chain verification, incident resolution.
- **`test_verification.py`**: Review queue triage, authoritative decision records.

---

## 5. Coding Standards

- **Python:** Strict PEP 8, Pydantic V2 schemas for I/O validation, SQLAlchemy 2.0 type hints.
- **TypeScript:** Strict type checking (`noImplicitAny: true`, strict null checks), Tailwind CSS utility-first classes, Lucide icons.
