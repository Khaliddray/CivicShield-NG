# CIVICSHIELD NG — REST API SPECIFICATION

**Base URL:** `/api/v1`  
**Protocol:** HTTPS / JSON  
**Authentication Scheme:** HTTP Bearer JWT (`Authorization: Bearer <token>`)

---

## 1. Unified Response Envelope

### Success Response Format
```json
{
  "success": true,
  "data": { ... },
  "message": "Human readable status summary",
  "timestamp": "2026-11-04T12:00:00Z"
}
```

### Error Response Format
```json
{
  "success": false,
  "error_code": "ENTITY_NOT_FOUND",
  "message": "Report with reference CS-20261104-ABC123 does not exist.",
  "details": {},
  "timestamp": "2026-11-04T12:00:00Z"
}
```

---

## 2. API Endpoint Catalog

### 2.1. Authentication & Access (`/api/v1/auth`)

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `POST` | `/auth/register` | Public | Register citizen account with Nigerian state |
| `POST` | `/auth/login` | Public | Authenticate with email/password; returns JWT |
| `POST` | `/auth/refresh` | Public | Exchange refresh token for new access token |
| `GET` | `/auth/me` | Authenticated | Retrieve profile, assigned roles & permissions |

### 2.2. Citizen Reporting (`/api/v1/reports`)

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `POST` | `/reports/submit` | Public / Multipart | Submit suspicious claim with optional media |
| `GET` | `/reports/track/{reference_number}` | Public | Look up investigation status by reference |
| `GET` | `/reports/me` | Authenticated | List all submissions by current user |
| `GET` | `/reports` | Analyst / Admin | List all reports with state/platform filters |
| `GET` | `/reports/{id}` | Analyst / Admin | Get full report details with evidence metadata |

### 2.3. Certified Gazette Registry (`/api/v1/registry`)

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/registry/documents` | Public | Search certified electoral documents & gazettes |
| `GET` | `/registry/documents/{code}` | Public | Retrieve official document by canonical code |
| `POST` | `/registry/verify-hash` | Public | Compute SHA-256 and verify claim against registry |
| `POST` | `/registry/documents` | Verification Officer | Authenticate & publish new official announcement |

### 2.4. AI Misinformation Engine (`/api/v1/ai`)

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `POST` | `/ai/analyze-claim` | Public | Analyze text claim, extract category & similarity |
| `POST` | `/ai/reports/{id}/process-claims` | Analyst / Admin | Trigger atomic claim decomposition for report |

### 2.5. Verification Review Queue (`/api/v1/verification`)

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/verification/queue` | Verification Officer | Retrieve pending human review queue items |
| `POST` | `/verification/claims/{id}/decision` | Verification Officer | Record authoritative verification decision |
| `GET` | `/verification/claims/{id}/history` | Verification Officer | Audit trail of review history for claim |

### 2.6. Early Warnings & Notifications (`/api/v1/alerts`)

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/alerts/feed/active` | Public | Retrieve active high & critical advisories |
| `POST` | `/alerts/draft` | Verification Officer | Draft early warning with target state/scope |
| `POST` | `/alerts/{id}/approve` | Verification Officer | Dual-key sign-off & broadcast to channels |
| `POST` | `/alerts/{id}/withdraw` | Verification Officer | Supersede or withdraw active early warning |
| `GET` | `/alerts/preferences` | Authenticated | Retrieve user notification preferences |
| `PUT` | `/alerts/preferences` | Authenticated | Update state/severity broadcast filters |

### 2.7. Coordinated Narrative Detection (`/api/v1/narratives`)

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/narratives/clusters` | Analyst / Admin | List narrative clusters with velocity index |
| `GET` | `/narratives/clusters/{id}` | Analyst / Admin | Detailed cluster breakdown with grouped reports |
| `GET` | `/narratives/network-graph` | Analyst / Admin | Graph nodes & links for relationship explorer |

### 2.8. Security & Cryptographic Audit (`/api/v1/security`)

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/security/audit-logs` | Security Officer | Query tamper-evident audit ledger entries |
| `POST` | `/security/audit-logs/verify-ledger` | Security Officer | Verify unbroken cryptographic hash chain |
| `GET` | `/security/events` | Security Officer | List security technical incidents |
| `POST` | `/security/events/{id}/resolve` | Security Officer | Resolve incident with officer signature notes |
| `GET` | `/security/metrics` | Security Officer | Platform security KPIs and ledger integrity |
