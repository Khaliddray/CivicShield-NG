# CIVICSHIELD NG — CENTRAL AGENT & TEAM ENGINEERING INSTRUCTIONS (`AGENT.md`)

> **Document Version:** 1.0.0  
> **Status:** Active / Authoritative  
> **Last Verified:** November 2026  
> **Target Audience:** Antigravity AI Agents, Technical Leads, and Engineering Team Members (Backend, AI, Frontend)

---

## 1. OPERATIONAL MANDATE & PURPOSE

This document serves as the single source of truth for all autonomous AI coding agents (Antigravity) and human software engineers contributing to **CivicShield NG**. Every technical choice, pull request, code modification, and architecture proposal must align with the guidelines, ownership boundaries, and invariants specified herein.

**Core Directive:** Deliver a reliable, secure, accessible, evidence-based, and demonstrable MVP within a strict **7-day deadline**. Optimize for end-to-end functionality, high test coverage, and defensible security rather than speculative, unintegrated features.

---

## 2. PROJECT CONTEXT & CORE VISION

### 2.1. Mission Statement
**CivicShield NG** is a nonpartisan, AI-powered Electoral Information Integrity and Threat Intelligence Platform designed to protect Nigeria's democratic information ecosystem. 

The platform bridges Nigerian citizens, civil society fact-checkers, and electoral institutions (such as INEC). It empowers citizens to report suspicious announcements, provides automated AI-assisted claim extraction and cross-referencing against certified gazettes, and equips institutional officers with a human-in-the-loop Command Centre to verify claims, monitor emerging narrative clusters, issue dual-key early warning advisories, and audit every database state change via a cryptographic ledger.

### 2.2. Core Tagline
> **"Detect early. Verify intelligently. Protect securely. Respond collectively."**

### 2.3. Dual Core Experiences

```
                                  CIVICSHIELD NG
                                        │
             ┌──────────────────────────┴──────────────────────────┐
             ▼                                                     ▼
   CIVICSHIELD CITIZEN PORTAL                           CIVICSHIELD COMMAND CENTRE
  (Public & Citizen Facing)                         (Institutional Review & Analysts)
  • Anonymous or Verified Reporting                 • Incoming Report Intake & Triage
  • CS-YYYYMMDD-XXXXXX Tracking                     • Verification Review Queue (Claims)
  • Gazette Registry Search & Hash Verifier         • Narrative Pulse (Cluster Velocity)
  • CivicShield AI Grounded Q&A                     • Dual-Key Early Warning Broadcasting
  • Multi-Channel Early Warning Feed                • Tamper-Evident SHA-256 Ledger Audit
  • CivicShield Access (Voice & A11y)               • Threat Incident Mitigation
```

#### A. CivicShield Citizen Portal (`CitizenHome.tsx`)
1. **Low-Friction Reporting:** Citizens submit suspicious announcements, claims, images, audio, or video without mandatory account creation.
2. **Privacy Assurance:** Citizen IP addresses are salted and hashed using SHA-256 (`backend/app/modules/reporting/service.py`). Zero personally identifiable information (PII) is exposed.
3. **Reference Tracking:** Generates a canonical tracking code (`CS-YYYYMMDD-XXXXXX`) to inspect verification status in real time without login.
4. **Certified Gazette Registry & Hash Verifier:** Search authenticated election notices and verify cryptographic SHA-256 hashes of digital notices to detect document tampering.
5. **Conversational CivicShield AI:** Interactive assistant that answers civic questions grounded strictly in official gazettes, admitting uncertainty when documents do not exist.
6. **Active Early Warning Feed:** Nationwide and state-specific advisories detailing verified debunks and official clarifications.
7. **CivicShield Access:** Multi-modal interface supporting screen readers, keyboard navigation, high contrast, text scaling, and voice input/output.

#### B. CivicShield Command Centre (`CommandDashboard.tsx`)
1. **Threat Intelligence Overview:** Real-time metrics tracking submission velocity, pending triage queues, high-risk states, and cryptographic ledger health.
2. **Verification Review Queue:** Institutional workflow where Verification Officers examine extracted atomic claims, cite certified gazettes, and record binding decisions (`VERIFIED`, `CONTRADICTED`, `INSUFFICIENT_EVIDENCE`).
3. **Narrative Pulse:** Real-time semantic clustering engine that groups similar submissions, tracks velocity scores across Nigerian states, and visualizes network relationship graphs.
4. **Official Gazette Management:** Publish authenticated releases with SHA-256 checksums and versioning.
5. **Early Warning Broadcast Centre:** Dual-key approval model (`WARN-YYYY-XXXX`) distributing early warning advisories across citizen feeds.
6. **Tamper-Evident Audit Ledger:** Cryptographic hash-chained ledger linking every transaction to a genesis block with real-time tampering detection.

---

## 3. CORE PRODUCT FEATURES

### 3.1. AI-Assisted Information Verification
- **Claim Extraction:** Decomposes citizen submissions into discrete atomic factual statements.
- **Official Grounding:** Matches extracted claims against the authenticated `OfficialDocument` registry.
- **Defensive Pre-Processing:** Runs adversarial prompt injection defense (`PromptDefense`) before sending text to AI models.
- **Strict Verification Taxonomy:**
  - `UNVERIFIED`: Ingested, awaiting triage or processing.
  - `UNDER_REVIEW`: AI claims extracted, pending human review.
  - `VERIFIED`: Confirmed true against official documentation by human officer.
  - `CONTRADICTED`: Confirmed false or fabricated against official documentation by human officer.
  - `INSUFFICIENT_EVIDENCE`: Evaluated, but available evidence cannot prove or disprove the claim.
  - `WITHDRAWN`: Claim or report superseded or retracted.
- **Invariant:** AI confidence scores are *never* presented as proof of truth or falsity. Human officer review is mandatory before any public status changes.

### 3.2. CivicShield Live — Real-Time Intelligence & Flagship "Narrative Pulse"
- **Narrative Pulse Dashboard:** Groups similar submissions across Nigerian states into unified narrative clusters.
- **Metrics Tracked:** Report count, distinct states affected, propagation velocity index, first detected timestamp, and last activity timestamp.
- **Relationship Graph:** Generates graph nodes (clusters, reports) and similarity edges for network visualization.
- **Live Updates:** Frontend polls backend endpoints (`/api/v1/narratives/clusters` and `/api/v1/reports`) on a configurable interval (default: 10s), upgradeable to WebSockets.
- **Ethical Invariant:** *Similar reports do not automatically prove coordinated disinformation, malicious intent, or common authorship.* Clusters represent narrative recurrence, not criminal attribution.

### 3.3. CivicShield Access — Accessibility
Accessibility is a core architectural pillar, not an afterthought:
- **Visual:** High contrast mode toggle, text size scaling (`sm`, `md`, `lg`, `xl`), full keyboard navigation (`tabindex`, visible focus rings), descriptive ARIA labels, semantic HTML landmarks.
- **Hearing:** Visual notification banners, full textual transcripts for all media, no sound-only alerts.
- **Motor:** Large clickable touch targets (minimum 44x44px), zero reliance on drag-and-drop gestures, full keyboard traversal.
- **Cognitive:** Plain language summaries, clear verification badges with distinctive colors and shapes, minimal clutter.
- **Voice I/O:** Citizen portal voice input using browser Speech Recognition (with graceful fallback to text) and optional Text-to-Speech (TTS) synthesis for read-aloud responses.

### 3.4. Multilingual Civic Information
- Prioritize **English** and **Nigerian Pidgin** for the MVP.
- All machine translations must be clearly labeled: `"Machine Translation (Nigerian Pidgin) — Official source is in English"`.
- Official legal gazettes must retain their canonical English text alongside any localized translations.
- Do not claim support for languages that have not been thoroughly tested.

### 3.5. Official Electoral Information Navigator
- Conversational assistant embedded in the Citizen Portal.
- Uses retrieval-augmented search over certified gazettes and FAQs (`/api/v1/registry/search`).
- When evidence is missing: *"I cannot find certified information in the official registry regarding this schedule. Please check back as official INEC releases are updated."*

### 3.6. Alerts & Early Warning Notification Engine
- **Dual-Key Protocol:** Analysts can draft an alert (`POST /api/v1/alerts`), but broadcast requires approval by a Lead Verification Officer or Administrator (`POST /api/v1/alerts/{id}/approve`).
- **Targeting:** Scope by `NATIONAL` or `STATE_SPECIFIC` (validated against the 36 Nigerian states + FCT).
- **Withdrawal & Clarification:** Active alerts can be withdrawn with mandatory recorded justifications (`POST /api/v1/alerts/{id}/withdraw`).
- **AI Independence:** Alerts are *never* auto-published by AI models.

### 3.7. Security, Privacy & Cryptographic Auditability
- **Authentication & RBAC:** Argon2id password hashing, PyJWT bearer tokens, 5 granular system roles (`CITIZEN`, `ANALYST`, `VERIFICATION_OFFICER`, `SECURITY_OFFICER`, `ADMINISTRATOR`).
- **Citizen Privacy:** Client IP addresses are combined with a server secret salt and hashed with SHA-256. Zero citizen PII is exposed to analysts.
- **Tamper-Evident Ledger:** Every significant database event (claim verification, alert broadcast, user authentication, role assignment) appends an immutable block containing `sha256(previous_hash + entry_data)`. The endpoint `POST /api/v1/security/verify-ledger` verifies the complete chain from genesis in real time.
- **Evidence Vault:** Uploaded media is validated for MIME type, file extension, and file size (max 25MB). Files are fingerprinted with SHA-256 upon disk ingestion.

---

## 4. ACTUAL REPOSITORY BLUEPRINT & TECHNOLOGY STACK

### 4.1. Inspected Stack Inventory

| Tier | Component | Technology & Version | Status |
|---|---|---|---|
| **Backend** | Framework | FastAPI 0.115+, Python 3.12+ (tested on 3.14) | Operational |
| **Backend** | ORM / DB Access | SQLAlchemy 2.0.36, Alembic 1.14 | Operational |
| **Backend** | Database (Local) | SQLite 3 with Write-Ahead Logging (`WAL`) & Foreign Keys | Operational (`civicshield.db`) |
| **Backend** | Database (Prod) | PostgreSQL 16+ via `psycopg2-binary` | Configured in `docker-compose.yml` |
| **Backend** | Cryptography / Auth | Argon2-cffi 23.1, PyJWT 2.10, Python `hashlib` | Operational |
| **Frontend** | Framework | React 18.3.1, TypeScript 5.7, Vite 6.1 | Operational |
| **Frontend** | Styling & UI | Tailwind CSS 3.4, Lucide Icons, Recharts 2.15 | Operational |
| **Frontend** | HTTP Client | Axios 1.7.9 (configured with JWT interceptors) | Operational |
| **AI Layer** | Architecture | Pluggable `BaseAIProvider` | Operational (`LocalHeuristicAIProvider`) |
| **Testing** | Test Runner | Python `unittest` via `run_tests.py` | 51/51 Tests Passing (100%) |

### 4.2. Backend Directory Topology (`backend/app/`)

```
backend/app/
├── main.py                     # FastAPI application factory, middleware, router mounts, health check
├── models.py                   # Central SQLAlchemy models registry for Alembic metadata
├── core/
│   ├── config.py               # Pydantic Settings (Environment variables, JWT, Upload configs)
│   ├── database.py             # SQLAlchemy engine, SessionLocal, WAL initialization, Base class
│   ├── dependencies.py         # FastAPI security dependencies (get_current_user, require_permission)
│   ├── exceptions.py           # Custom CivicShieldException hierarchy and global HTTP handlers
│   ├── init_db.py              # Schema migration runner and RBAC seed manager
│   ├── logging.py              # Structured logging utility
│   └── security.py             # Argon2id password hashing and PyJWT token generation/decoding
├── common/
│   ├── enums.py                # System enums (UserRoleType, VerificationDecision, AlertStatus, etc.)
│   ├── geo.py                  # Canonical 36 Nigerian States + FCT validator and geo dictionary
│   └── schemas.py              # Standard API envelopes (APIResponse[T], PaginatedResponse[T])
└── modules/
    ├── auth/                   # Registration, login, lockout defense, RBAC models and services
    ├── reporting/              # Citizen submissions, media uploads, SHA-256 IP hashing, report tracking
    ├── registry/               # Certified official documents, canonical SHA-256 indexing, hash verification
    ├── ai_engine/              # Prompt injection defense, atomic claim extractor, similarity engine
    │   └── providers/          # Pluggable BaseAIProvider, LocalHeuristicAIProvider (expandable to Gemini)
    ├── verification/           # Institutional triage queue, human authoritative decision recording
    ├── narratives/             # Coordinated narrative clustering, velocity scoring, relationship graph
    ├── notifications/          # Early warning drafting, dual-key signoff, citizen alert feeds
    └── security_audit/         # Cryptographic SHA-256 chained audit ledger, threat incident management
```

### 4.3. Frontend Directory Topology (`frontend/src/`)

```
frontend/src/
├── main.tsx                    # React root mount point
├── App.tsx                     # Top-level view router (Citizen Portal vs Command Centre)
├── index.css                   # Tailwind CSS styling and global styles
├── types/
│   └── index.ts                # TypeScript interfaces mirroring backend schemas
├── context/
│   └── AuthContext.tsx         # JWT token lifecycle, login/logout, user permissions state
├── api/
│   └── client.ts               # Axios instance with baseURL '/api/v1' and auth headers
└── components/
    ├── common/
    │   ├── Navbar.tsx          # Dual-experience switcher, Auth status, and modal trigger
    │   ├── AlertBanner.tsx     # Active early warning ticker banner (polls /alerts/active)
    │   └── AuthModal.tsx       # Institutional login / citizen registration modal
    ├── citizen/
    │   └── CitizenHome.tsx     # Citizen Portal (Report submission, Tracking, Gazette search, AI Chat)
    └── command/
        └── CommandDashboard.tsx# Institutional Command Centre (Overview, Queue, Narratives, Alerts, Audit)
```

---

## 5. THREE-MEMBER TEAM OWNERSHIP & BOUNDARIES

All three developers and any assisting AI agents must respect the strict ownership boundaries below.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          THREE-MEMBER TEAM MATRIX                           │
├──────────────────────┬──────────────────────────────┬───────────────────────┤
│ MEMBER 1             │ MEMBER 2                     │ MEMBER 3              │
│ Backend & Integration│ AI & Threat Intelligence     │ Frontend & Product    │
├──────────────────────┼──────────────────────────────┼───────────────────────┤
│ • FastAPI Router/Core│ • Claim Extraction           │ • Citizen Portal UI   │
│ • Database & Alembic │ • Semantic Similarity        │ • Command Dashboard   │
│ • Auth & RBAC        │ • Prompt Injection Defense   │ • Narrative Pulse UI  │
│ • Verification Engine│ • Source Grounding Engine    │ • CivicShield Access  │
│ • Alerts & Security  │ • Narrative Clustering Alg   │ • Voice I/O & Audio   │
│ • Cryptographic Chain│ • Provider Implementations   │ • Accessibility (a11y)│
└──────────────────────┴──────────────────────────────┴───────────────────────┘
```

### 5.1. Member 1 — Backend & Technical Integration Lead
- **Primary Modules:**
  - `backend/app/core/*` (database, dependencies, security, init_db)
  - `backend/app/modules/auth/*`
  - `backend/app/modules/reporting/*`
  - `backend/app/modules/registry/*`
  - `backend/app/modules/verification/*`
  - `backend/app/modules/notifications/*`
  - `backend/app/modules/security_audit/*`
  - `backend/tests/*` and `run_tests.py`
  - Docker and deployment configurations (`docker-compose.yml`, Dockerfiles)
- **Key Responsibilities:**
  1. Maintain database integrity, migrations (`alembic`), and WAL performance.
  2. Protect RBAC authorization guards and API security.
  3. Ensure evidence uploads are virus-safe, MIME-checked, and stored securely.
  4. Guarantee unbroken cryptographic chaining in the audit ledger.
  5. Run and verify all 51 test cases before any PR or merge.

### 5.2. Member 2 — AI & Threat Intelligence Engineer
- **Primary Modules:**
  - `backend/app/modules/ai_engine/*`
  - `backend/app/modules/ai_engine/providers/*`
  - `backend/app/modules/narratives/service.py` (Clustering and velocity algorithms)
  - Multilingual processing utilities
  - Speech-to-text / Audio transcription integration
- **Key Responsibilities:**
  1. Maintain and extend `BaseAIProvider` (e.g. adding `GeminiAIProvider` with fallback to `LocalHeuristicAIProvider`).
  2. Enhance atomic claim decomposition and prompt injection sanitization.
  3. Improve semantic similarity algorithms (Jaccard + embeddings) for **Narrative Pulse**.
  4. Ensure all AI responses communicate uncertainty, evidence citations, and mandatory human review requirements.
  5. Expose stable, documented Python methods consumed cleanly by Member 1's services.

### 5.3. Member 3 — Frontend & Product Engineer
- **Primary Modules:**
  - `frontend/src/components/*`
  - `frontend/src/context/*`
  - `frontend/src/types/index.ts`
  - `frontend/src/api/client.ts`
  - `frontend/index.html` and Tailwind CSS configurations
- **Key Responsibilities:**
  1. Deliver the responsive Citizen Portal and Institutional Command Centre.
  2. Implement **Narrative Pulse** real-time UI with cluster inspection and velocity trends.
  3. Implement **CivicShield Access** (high contrast toggle, text resizer, keyboard navigation, screen reader labels, plain language feedback).
  4. Build the Web Speech API voice recording and optional speech synthesis playback.
  5. Adhere strictly to the backend API contracts without inventing fictitious endpoints.

### 5.4. Team Coordination & Git Rules
1. **Feature Branches:** Work on dedicated branches (`feat/backend-*`, `feat/ai-*`, `feat/frontend-*`). Never push directly to `main` without running `python3 run_tests.py`.
2. **Contract First:** Agree on request/response JSON schemas in `schemas.py` and `types/index.ts` before integrating frontend and backend features.
3. **No Direct Overwriting:** Do not rewrite or restructure another member's working module without explicit coordination.
4. **Preserve Passing Tests:** The test suite must remain at 100% passing (51/51) after every change.

---

## 6. CANONICAL API CONTRACTS & DATA CONSISTENCY

All endpoints communicate under the prefix `/api/v1`.

### 6.1. Unified Response Envelope
Every response adheres to `APIResponse[T]`:
```json
{
  "success": true,
  "data": { ... },
  "message": "Operation completed successfully.",
  "errors": null,
  "timestamp": "2026-11-05T16:20:47.882706Z"
}
```

On validation failure or application error:
```json
{
  "success": false,
  "data": null,
  "message": "Human readable explanation of the error",
  "errors": [
    { "field": "nigerian_state", "issue": "'Atlantis' is not a recognized Nigerian State." }
  ],
  "timestamp": "2026-11-05T16:20:47.882706Z"
}
```

### 6.2. Verified Live Endpoint Catalog

| Module | Method | Endpoint Path | Access Level | Description |
|---|---|---|---|---|
| **Health** | `GET` | `/health` | Public | System and DB health check |
| **Auth** | `POST` | `/auth/register` | Public | Citizen account registration |
| **Auth** | `POST` | `/auth/login` | Public | Credentials authentication (JWT) |
| **Auth** | `POST` | `/auth/refresh` | Public | Refresh token rotation |
| **Auth** | `GET` | `/auth/me` | Authenticated | Retrieve current user profile and permissions |
| **Reporting** | `POST` | `/reports` | Public (Multipart) | Submit suspicious report with media |
| **Reporting** | `POST` | `/reports/submit` | Public (Multipart) | Canonical alias for report submission |
| **Reporting** | `GET` | `/reports/track/{ref}` | Public | Look up report status by tracking code |
| **Reporting** | `GET` | `/reports/my-reports` | Authenticated | List submissions by logged-in citizen |
| **Reporting** | `GET` | `/reports` | `reports:view_all` | Command Centre paginated report intake |
| **Reporting** | `GET` | `/reports/{id}` | `reports:view_all` | Detailed report with claims and evidence |
| **Registry** | `POST` | `/registry/documents` | `registry:manage` | Certify & publish official announcement |
| **Registry** | `POST` | `/registry/verify` | Public | Verify text/document against certified registry |
| **Registry** | `GET` | `/registry/search` | Public | Search authenticated electoral gazettes |
| **Registry** | `GET` | `/registry/documents/{code}` | Public | Get official document by canonical code |
| **AI Engine** | `POST` | `/ai/analyze-claim` | Public | Analyze text claim against certified registry |
| **AI Engine** | `POST` | `/ai/reports/{id}/analyze` | `claims:analyze` | Trigger claim extraction pipeline for report |
| **Verification**| `GET` | `/verification/queue` | `claims:verify` | Triage queue prioritized by urgency |
| **Verification**| `POST` | `/verification/decisions` | `claims:verify` | Record binding human verification decision |
| **Verification**| `GET` | `/verification/decisions/{id}`| Public / Auth | Inspect decision record and citations |
| **Verification**| `GET` | `/verification/claims/{id}` | Public / Auth | Inspect claim verification history |
| **Narratives** | `GET` | `/narratives/clusters` | `narratives:view` | List active clusters with velocity scores |
| **Narratives** | `GET` | `/narratives/clusters/{id}` | `narratives:view` | Inspect constituent reports of a cluster |
| **Narratives** | `GET` | `/narratives/graph` | `narratives:view` | Relationship graph nodes & similarity edges |
| **Narratives** | `POST` | `/narratives/scan` | `narratives:view` | Trigger clustering discovery scan |
| **Alerts** | `GET` | `/alerts/active` | Public | Retrieve verified active early warnings |
| **Alerts** | `POST` | `/alerts` | `alerts:create` | Draft early warning advisory |
| **Alerts** | `POST` | `/alerts/{id}/approve` | `alerts:approve` | Dual-key sign-off & broadcast |
| **Alerts** | `POST` | `/alerts/{id}/withdraw` | `alerts:withdraw`| Withdraw or supersede active alert |
| **Alerts** | `GET` | `/alerts/preferences` | Authenticated | Citizen alert preferences |
| **Alerts** | `PUT` | `/alerts/preferences` | Authenticated | Update state/severity alert preferences |
| **Security** | `GET` | `/security/audit-logs` | `audit:read` | Query tamper-evident audit ledger |
| **Security** | `POST` | `/security/verify-ledger`| `audit:read` | Cryptographically verify SHA-256 chain |
| **Security** | `GET` | `/security/events` | `security:manage` | List security threat events |
| **Security** | `POST` | `/security/events/{id}/resolve`| `security:manage` | Resolve security event with officer note |
| **Security** | `GET` | `/security/metrics` | `security:manage` | Real-time security and ledger health KPIs |

> **Architectural Note on Route Aliasing:**  
> The backend provides backward-compatible aliases for legacy documentation paths (e.g. `POST /reports/submit` and `POST /reports`). When adding new frontend calls, always use the canonical paths listed above.

---

## 7. RESPONSIBLE AI & ELECTORAL SAFETY INVARIANTS

These rules are non-negotiable and must be enforced by all agents and developers:

1. **Strict Nonpartisanship:** CivicShield NG is completely nonpartisan. The platform never expresses political preferences, scores candidates, or favors any political party.
2. **No Voter Profiling or Microtargeting:** No capability shall be created to infer, track, or label a citizen's political affiliation.
3. **No Autonomous Official Decisions:** AI models *never* autonomously mark a claim as `VERIFIED` or `CONTRADICTED` in the public registry. All authoritative decisions require human Verification Officer approval.
4. **No Autonomous Alert Broadcasting:** AI models *never* automatically publish or broadcast public alerts. All alerts require dual-key human authorization (`alerts:create` then `alerts:approve`).
5. **Correlation != Disinformation:** Similar reports clustered in **Narrative Pulse** do not inherently prove coordinated disinformation or malicious intent. System copy must state this clearly.
6. **Mandatory Citations & Evidence Grounding:** AI assessments must link to specific certified official gazettes. When no official document exists, the system must explicitly state that evidence is insufficient.
7. **No Hallucination of Electoral Directives:** The system must never fabricate polling times, collation procedures, or election results.
8. **Salted Anonymity:** Citizen IP addresses are hashed using `sha256(ip + salt)`. Raw IPs are never persisted in submission records.
9. **Synthetic Data Labeling:** All demonstration datasets, sample reports, and test claims must be clearly labeled as `"SIMULATED / DEMONSTRATION DATA"`.
10. **Zero Tampering with Electoral Infrastructure:** CivicShield operates strictly on public civic information and certified public gazettes. Never attempt to query private or restricted INEC databases.

---

## 8. SEVEN-DAY DELIVERY PRIORITIES (MVP SCOPE)

To ensure delivery within 7 days, work must follow strict prioritization:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        MVP SCOPE PRIORITIZATION                        │
├────────────────────────────────────────────────────────────────────────┤
│ [P0] ESSENTIAL (Days 1–3) — Must Work Flawlessly                       │
│  ✓ Full Backend & Frontend operational and integrated                  │
│  ✓ Citizen report submission with reference generation & media uploads │
│  ✓ Defensive claim extraction and source cross-referencing             │
│  ✓ Human Verification Review Queue with binding decisions              │
│  ✓ Dual-key Early Warning broadcasting & active citizen feed           │
│  ✓ Tamper-evident cryptographic audit ledger verification              │
│  ✓ 100% passing test suite (51/51 tests passing)                       │
├────────────────────────────────────────────────────────────────────────┤
│ [P1] STANDOUT CAPABILITIES (Days 4–5) — High Impact Differentiation    │
│  • Narrative Pulse: Grouped report view, velocity score, inspection    │
│  • CivicShield Access: High contrast, text scaler, keyboard traversal  │
│  • Voice I/O: Speech recognition input & TTS response playback         │
│  • Live dashboard refresh (10s polling interval)                       │
├────────────────────────────────────────────────────────────────────────┤
│ [P2] TIME-PERMITTING ONLY (Days 6–7) — Do NOT Block P0 or P1           │
│  • Nigerian Pidgin localization toggle for Citizen Portal              │
│  • Low-bandwidth / PWA offline report caching                          │
│  • External WhatsApp gateway webhook simulation                        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 9. TESTING, VERIFICATION & QUALITY ASSURANCE

### 9.1. Test Execution Commands
The test suite is unified and runs against SQLite WAL in memory or local test database:
```bash
# Run all 51 module and end-to-end acceptance tests
python3 run_tests.py
```

### 9.2. Master Acceptance Criteria (Workflows A Through G)
All 7 institutional workflows in `backend/tests/test_e2e_workflows.py` must pass 100%:
- **Workflow A:** Citizen submits suspicious notice &rarr; receives tracking code (`CS-YYYYMMDD-XXXXXX`).
- **Workflow B:** AI neutralizes adversarial prompt injection, extracts atomic claims, and queries registry.
- **Workflow C:** Human Verification Officer inspects queue, cites certified gazette, and marks `CONTRADICTED`.
- **Workflow D:** System drafts early warning advisory (`WARN-YYYY-XXXX`).
- **Workflow E:** Lead Officer signs off &rarr; advisory broadcasts to active citizen alert banner.
- **Workflow F:** Security Officer inspects tamper-evident audit ledger &rarr; verifies 100% unbroken cryptographic chain.
- **Workflow G:** Multi-state reports automatically group into Narrative Clusters with velocity metrics.

### 9.3. Quality Standards for Code Additions
- Every new API endpoint must have a corresponding test case in `backend/tests/`.
- Every frontend API call must handle network errors gracefully and present human-readable messages.
- New database tables or column modifications must include an Alembic migration script.

---

## 10. AGENT OPERATING PROTOCOL

When an autonomous agent receives an instruction:

### The 10-Step Execution Cycle
1. **Understand Request:** Identify the requested feature and its acceptance criteria.
2. **Inspect First:** Check relevant existing files (`read_file`, `find`, `grep`). Never assume a file exists.
3. **Check Dependencies:** Identify affected modules, schemas, and tests before modifying code.
4. **Formulate Plan:** Outline the minimal, precise change required.
5. **Implement Incrementally:** Use `edit_file` or `write_file` cleanly. Preserve all existing working code, docstrings, and comments.
6. **Preserve Boundaries:** Respect Member 1, Member 2, and Member 3 ownership rules.
7. **Run Tests:** Execute `python3 run_tests.py` and ensure all 51 tests pass.
8. **Verify UI / Endpoint:** Test the endpoint with `curl` or inspect frontend build output (`npm run build`).
9. **Review Output:** Confirm no side-effects or regressions occurred.
10. **Report Transparently:** State what changed, what tests ran, and any next steps.

### Strict Prohibitions ("NEVER" List)
- **NEVER** delete, wipe, or drop the local database (`civicshield.db`) to fix an unrelated issue.
- **NEVER** overwrite existing working files with speculative scaffolding or boilerplate.
- **NEVER** introduce Redis, Celery, or external cloud infrastructure unless explicitly directed.
- **NEVER** invent API routes that do not exist in the backend.
- **NEVER** disable, skip, or mock out failing tests to make a build pass.
- **NEVER** expose un-hashed citizen IP addresses or personal identifiable information.
- **NEVER** bypass role-based access control (`require_permission`) checks.
- **NEVER** claim a feature works without verifying it through a test or execution command.
