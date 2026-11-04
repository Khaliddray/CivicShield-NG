# CHANGELOG — CIVICSHIELD NG

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-11-04

### Added
- **Core Architecture:** Modular monolith backend powered by FastAPI, SQLAlchemy 2.0, Alembic, and Pydantic V2.
- **Authentication & RBAC:** Argon2id password hashing, JWT bearer tokens, 5-tier role hierarchy (`CITIZEN`, `ANALYST`, `VERIFICATION_OFFICER`, `SECURITY_OFFICER`, `ADMINISTRATOR`), and brute-force lockout defenses.
- **Citizen Reporting Engine:** Low-friction submission system generating unique reference numbers (`CS-YYYYMMDD-XXXXXX`), salted SHA-256 submitter IP privacy hashing, and multi-format evidence file upload.
- **Certified Gazette Registry:** Official information registry computing canonical SHA-256 document hashes to detect tampering and certify authentic electoral notices.
- **AI Misinformation Intelligence:** Multi-pattern prompt injection defense filter, atomic claim decomposition, electoral lexicon categorization, and registry cross-matching.
- **Institutional Verification Centre:** Human verification queue for officers to record authoritative decisions (`VERIFIED`, `CONTRADICTED`, `INSUFFICIENT_EVIDENCE`) citing official gazettes.
- **Early Warning & Notification Engine:** Dual-key approval broadcast system (`WARN-YYYY-XXXX`), geographic targeting across 36 Nigerian states and FCT, and 4-hour suppression window.
- **Coordinated Narrative Detection:** Jaccard-based narrative clustering, propagation velocity index, multi-state spread tracking, and threat indicators.
- **Database Security & Tamper-Evident Audit Ledger:** Cryptographic SHA-256 chained audit trail linked to a verifiable genesis hash with automated integrity validation and security incident resolution tools.
- **Frontend Application:** Modern React 18 SPA built with Vite, TypeScript, Tailwind CSS, Lucide icons, and Recharts, offering dual experiences (CivicShield AI & CivicShield Command Centre).
- **Documentation & Containers:** Complete architectural, database, security, API, deployment, and development documentation along with production Dockerfiles and docker-compose.
