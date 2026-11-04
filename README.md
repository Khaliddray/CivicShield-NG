# CIVICSHIELD NG — ELECTORAL INFORMATION INTEGRITY & THREAT INTELLIGENCE PLATFORM

<div align="center">

![CivicShield NG Banner](https://img.shields.io/badge/CivicShield_NG-Electoral_Integrity_Infrastructure-0D3B2E?style=for-the-badge&logo=shield)
![Python 3.12](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React 18](https://img.shields.io/badge/React-18.3+-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-5.7+-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![Tests Passing](https://img.shields.io/badge/Tests-50%2F50%20Passing%20(100%25)-10B981?style=for-the-badge&logo=checkmarx)
![License](https://img.shields.io/badge/License-MIT-008751?style=for-the-badge)

**"Detect early. Verify intelligently. Protect securely. Respond collectively."**

</div>

---

## 1. Executive Summary & Problem Statement

In electoral democracies, the information environment during voting periods is vulnerable to coordinated manipulation, synthetic media (deepfakes), forged institutional announcements, and targeted voter disenfranchisement. In Nigeria, rumors claiming polling postponements, fabricated collation figures, or fake administrative gazettes circulate virally via messaging groups before fact-checkers can respond.

**CivicShield NG** is a civic technology platform that bridges the gap between citizens and electoral authorities. It provides an immediate citizen reporting and cryptographic verification portal while equipping verified institutions, fact-checkers, and security officers with an intelligence Command Centre for coordinated narrative tracking, dual-key early warning broadcasts, and tamper-evident audit monitoring.

---

## 2. Dual Core Product Vision

CivicShield NG delivers two deeply synchronized experiences powered by a unified modular backend:

### A. CivicShield AI — Citizen-Facing Intelligence Portal
*Designed for web accessibility and future WhatsApp/Telegram conversational gateways.*
- **Low-Friction Reporting:** Submit suspicious electoral announcements, photos, screenshots, voice notes, and videos without mandatory registration.
- **Privacy Assurance:** Citizen IP addresses are salted and hashed with SHA-256; zero personal identifiable information (PII) is exposed.
- **Reference Tracking:** Generates a unique tracking reference code (`CS-YYYYMMDD-XXXXXX`) to inspect review status in real-time.
- **Official Gazette Registry & Hash Verifier:** Search authenticated election notices and compute SHA-256 hashes on the fly to detect document tampering.
- **Conversational AI Assistant:** Ask questions about official voting timetables and receive neutral, evidence-backed answers grounded in certified gazettes.
- **Active Early Warning Banner:** Real-time nationwide and state-specific warnings with official debunk clarifications.

### B. CivicShield Command Centre — Institutional Dashboard
*Restricted to authorized Analysts, Verification Officers, Security Officers, and Administrators.*
- **Threat Intelligence Overview:** Real-time KPIs tracking citizen report intake, pending review queues, narrative velocity scores, and ledger health.
- **Verification Review Queue:** Institutional workflow where human Verification Officers examine extracted claims, compare with certified official gazettes, and issue authoritative decisions (`VERIFIED`, `CONTRADICTED`, `INSUFFICIENT_EVIDENCE`).
- **Coordinated Narrative Detection:** Narrative clustering algorithm identifying multi-state amplification patterns, propagation velocity indices, and network relationship graphs.
- **Official Registry Management:** Publish authenticated press releases, notices, and directives with canonical cryptographic fingerprints.
- **Early Warning Broadcast Centre:** Dual-key approval model (`WARN-YYYY-XXXX`) distributing early warning advisories across in-app feeds and mobile push channels.
- **Tamper-Evident Audit Ledger:** Cryptographic hash-chained audit ledger linking every consequential database transaction to a verifiable genesis block with real-time tampering detection.

---

## 3. High-Level System Architecture

```
+-----------------------------------------------------------------------------------+
|                                 USER EXPERIENCES                                  |
|   +---------------------------------------+  +--------------------------------+   |
|   |     CivicShield AI (Citizen)         |  | CivicShield Command Centre     |   |
|   |  - Report Ingestion & Media Upload    |  |  - Threat KPIs & Velocity Map  |   |
|   |  - Public Report Tracker              |  |  - Verification Review Queue   |   |
|   |  - Certified Gazette Registry Search  |  |  - Coordinated Narrative Graph |   |
|   |  - Conversational AI Assistant        |  |  - Dual-Key Warning Broadcast  |   |
|   |  - Active Early Warning Feed          |  |  - Tamper-Evident Ledger Audit |   |
|   +---------------------------------------+  +--------------------------------+   |
+------------------------------------------+----------------------------------------+
                                           | HTTPS / JSON (REST API)
+------------------------------------------v----------------------------------------+
|                            FASTAPI BACKEND CORE                                   |
|   +---------------------------------------------------------------------------+   |
|   | API Router Layer: /api/v1 (Prefix-routed, Pydantic V2 validated)          |   |
|   +---------------------------------------------------------------------------+   |
|   | Security & Guard Layer: JWT Bearer, Argon2id, RBAC Guards, Prompt Defense |   |
|   +---------------------------------------------------------------------------+   |
|   | Domain Service Modules:                                                   |   |
|   |  1. Auth & RBAC Service (Brute-force Lockout, Token Lifecycle)            |   |
|   |  2. Reporting Service (CS-YYYYMMDD-XXXXXX, IP Salted Hashing, Uploads)    |   |
|   |  3. Registry Service (Canonical SHA-256 Hashing, Tamper Detection)        |   |
|   |  4. AI Intelligence Engine (Jaccard Similarity, Intent & Contradiction)  |   |
|   |  5. Verification Centre Service (Queue Triage, Authoritative Decisions)   |   |
|   |  6. Early Warning Engine (WARN-YYYY-XXXX, Dual-Key Approval, Geo Targets)  |   |
|   |  7. Narrative Intelligence (Jaccard Clustering, Velocity Scores, Graph)   |   |
|   |  8. Security & Audit Service (SHA-256 Chained Ledger, Threat Incidents)   |   |
|   +---------------------------------------------------------------------------+   |
+------------------------------------------+----------------------------------------+
                                           | SQLAlchemy 2.x (Parameterized ORM)
+------------------------------------------v----------------------------------------+
|                           PERSISTENCE & STORAGE                                   |
|  - Relational Database: SQLite with WAL & Foreign Keys (Dev) / PostgreSQL (Prod)  |
|  - Storage Vault: Protected Media Vault with SHA-256 Fingerprinting               |
|  - Cryptographic Chain: Immutable Audit Ledger with Genesis Chaining              |
+-----------------------------------------------------------------------------------+
```

---

## 4. Master Acceptance Workflows (MVP A Through G)

CivicShield NG has been verified against the seven core end-to-end institutional workflows:

| Workflow | Description | Status |
|---|---|---|
| **Workflow A** | Citizen submits suspicious election notice with media &rarr; receives unique tracking reference `CS-YYYYMMDD-XXXXXX`. | Verified |
| **Workflow B** | AI engine defends against prompt injections, extracts atomic claims, and cross-references against the Certified Gazette Registry. | Verified |
| **Workflow C** | Verification Officer triages pending queue, compares claim against certified gazette, and issues authoritative `CONTRADICTED` decision. | Verified |
| **Workflow D** | System auto-drafts early warning (`WARN-YYYY-XXXX`), requiring dual-key institutional approval prior to broadcast. | Verified |
| **Workflow E** | Authorized officer approves warning &rarr; advisory broadcasts to citizen feed with official debunk clarification. | Verified |
| **Workflow F** | Security Officer inspects tamper-evident audit ledger &rarr; verifies 100% unbroken cryptographic SHA-256 chain. | Verified |
| **Workflow G** | Correlated reports across states automatically cluster into Coordinated Narratives with velocity scoring. | Verified |

---

## 5. Technology Stack

- **Backend:** Python 3.12+, FastAPI, SQLAlchemy 2.0 (Type-annotated), Alembic, Pydantic V2, Argon2-cffi, PyJWT, Pillow, HTTPX.
- **Frontend:** React 18, TypeScript, Tailwind CSS, Vite, Lucide Icons, Recharts, Axios.
- **Persistence:** SQLite 3 with Write-Ahead Logging (`PRAGMA journal_mode=WAL;`) and foreign keys locally; PostgreSQL 16+ in production.
- **Container Infrastructure:** Docker, Docker Compose, Multi-stage builds, Nginx reverse proxy.

---

## 6. Quickstart Guide

### 6.1. Running the Backend

```bash
# 1. Initialize database and seed RBAC roles & permissions
python3 -c "from backend.app.core.init_db import init_database; init_database()"

# 2. Launch FastAPI development server
python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 6.2. Running the Frontend

```bash
# 1. Navigate to frontend directory and install dependencies
cd frontend
npm install

# 2. Start Vite development server
npm run dev
```
Open `http://localhost:5173` in your browser.

### 6.3. Running the Test Suite

```bash
# Run the unified test runner executing all 50 module tests
python3 run_tests.py
```

### 6.4. Running with Docker Compose

```bash
# Build and deploy the full stack (FastAPI, React, PostgreSQL 16, Redis)
docker compose up -d --build
```

---

## 7. Project Documentation

Comprehensive engineering documentation is available in the [`docs/`](./docs) folder:
- [System Architecture Specification](./docs/ARCHITECTURE.md)
- [Database Schema & Data Dictionary](./docs/DATABASE.md)
- [Cybersecurity & Threat Defense Architecture](./docs/SECURITY.md)
- [REST API Reference & OpenAPI Specification](./docs/API.md)
- [Production Deployment Guide](./docs/DEPLOYMENT.md)
- [Local Development Guide](./docs/DEVELOPMENT.md)
- [Changelog](./CHANGELOG.md)

---

## 8. License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
