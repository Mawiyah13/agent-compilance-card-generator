# Implementation Plan - Agent Compliance Card Generator

This document outlines the detailed architecture, database design, backend services, frontend interface, deployment configuration, and testing strategy for building a production-ready Agent Compliance Card Generator.

## Goal Description
The objective is to create an enterprise-grade AI Governance & Compliance platform that generates **Agent Compliance Cards** from three inputs:
1. **Agent Config** (JSON/YAML)
2. **Tool Manifest** (JSON/YAML)
3. **Runtime Trace** (TXT/JSON)

The resulting Compliance Cards document vital compliance information, including:
- **Governance**: Purpose, Scope, LLM & Version, Prompt Info, Tool Inventory, Operations, Data Access, Data Sources, Decision Authority, Human Oversight.
- **Risk & Security**: Risk Classification, Known Limitations, Incident Contact.
- **Metadata**: Audit Metadata, Timestamp, Version, Confidence Score.

The application features:
- **Regulation Mapping**: Mapping configurations and tools to EU AI Act Art.13, NIST AI RMF Govern, and ISO/IEC 42001.
- **Completeness Checker**: Verification of fields, identification of placeholder text, and calculation of a completeness score.
- **Card Versioning & Diffing**: Automatically tracking versions and recalculating compliance metrics when LLM, tools, permissions, decision authority, data sources, or risks change.
- **Export**: Professional PDF export and structured JSON export.
- **UI**: High-end enterprise dashboard inspired by Stripe, Elastic, and Grafana (using the specified dark aesthetic palette).
- **Auth**: JWT-based Authentication with Access/Refresh tokens and Role-Based Access Control (RBAC).

---

## User Review Required

> [!IMPORTANT]
> The database requires **PostgreSQL** and **Redis**. Ensure these services are running locally or via Docker Compose during development. We will provide a complete Docker Compose file.

> [!WARNING]
> Production deployment is configured using **Terraform** targeting **AWS ECS Fargate**. The Terraform setup assumes standard AWS credentials are provided via environment variables.

---

## Proposed Changes

We will create a structured layout inside the workspace directory:

```
agent-compliance-card-generator/
├── backend/                  # FastAPI Application
│   ├── app/
│   │   ├── api/              # REST Endpoints (v1)
│   │   ├── core/             # Configuration, Security (JWT, RBAC), Database setup
│   │   ├── models/           # SQLAlchemy DB Models (Card, Version, User, AuditLog)
│   │   ├── schemas/          # Pydantic Schemas
│   │   ├── services/         # Business Logic (Card parser, Checker, PDF export, OpenAI service)
│   │   ├── tests/            # Pytest test cases
│   │   └── main.py           # FastAPI entrypoint
│   ├── Dockerfile
│   ├── requirements.txt
│   └── alembic.ini
├── frontend/                 # React 19 Frontend
│   ├── src/
│   │   ├── components/       # Shared UI (Cards, Tables, Charts, Buttons)
│   │   ├── hooks/            # TanStack Query & Hooks
│   │   ├── store/            # Zustand state
│   │   ├── pages/            # Dashboard, Card Details, Audit Logs, Settings
│   │   ├── utils/            # Parsers, diff helpers
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── Dockerfile
├── terraform/                # Infrastructure-as-code
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
├── nginx/                    # Production Reverse Proxy
│   └── nginx.conf
├── .github/
│   └── workflows/
│       └── ci-cd.yml         # GitHub Actions CI/CD pipeline
├── docker-compose.yml        # Development & Orchestration
├── README.md                 # Documentation
└── architecture.md           # Architecture, ER diagrams & API specs
```

### Database Schema (ER Design)
- **`users`**: `id`, `email`, `hashed_password`, `role` (Admin, Auditor, Developer), `is_active`, `created_at`, `updated_at`.
- **`compliance_cards`**: `id`, `name`, `current_version_id`, `created_at`, `updated_at`, `created_by_id`.
- **`card_versions`**: `id`, `card_id`, `version` (semver), `config_input` (JSON), `tool_manifest_input` (JSON), `runtime_trace_input` (Text), `card_data` (JSON - holding compiled card fields), `completeness_score`, `risk_classification`, `confidence_score`, `created_at`, `created_by_id`.
- **`regulation_mappings`**: `id`, `version_id`, `framework` (EU AI Act, NIST, ISO), `status` (Compliant, Partially Compliant, Non-Compliant), `details` (JSON).
- **`audit_logs`**: `id`, `user_id`, `action`, `details` (JSON), `ip_address`, `timestamp`.

---

### Backend Components

#### [NEW] [backend/requirements.txt](file:///c:/Users/Admin/Desktop/agent-compilance-card-generator/backend/requirements.txt)
Contains backend dependencies: `fastapi`, `uvicorn`, `sqlalchemy`, `asyncpg`, `redis`, `pydantic`, `pyjwt`, `passlib`, `bcrypt`, `python-multipart`, `fpdf2` (or `weasyprint` / `reportlab` for PDF generation), `openai`, `pytest`, `pytest-asyncio`, `pyyaml`.

#### [NEW] [backend/app/core/config.py](file:///c:/Users/Admin/Desktop/agent-compilance-card-generator/backend/app/core/config.py)
System environment configuration using Pydantic settings. Handles DB connection pooling, Redis caching parameters, JWT secrets, and OpenAI API settings.

#### [NEW] [backend/app/core/security.py](file:///c:/Users/Admin/Desktop/agent-compilance-card-generator/backend/app/core/security.py)
JWT creation/decoding, password hashing, and role verification middleware.

#### [NEW] [backend/app/models/](file:///c:/Users/Admin/Desktop/agent-compilance-card-generator/backend/app/models/)
SQLAlchemy models matching the database schema.

#### [NEW] [backend/app/services/compliance.py](file:///c:/Users/Admin/Desktop/agent-compilance-card-generator/backend/app/services/compliance.py)
Engine for parsing inputs and auto-generating fields (via OpenAI structure extraction). Runs the **Completeness Checker** and **Regulation Mapping** rules (e.g., matching tool manifest/permissions to EU AI Act high-risk criteria, data access to ISO 42001, etc.).

#### [NEW] [backend/app/services/pdf_generator.py](file:///c:/Users/Admin/Desktop/agent-compilance-card-generator/backend/app/services/pdf_generator.py)
Service utilizing `reportlab` or `fpdf2` to construct a professional, high-fidelity PDF report of the compliance card using our theme colors.

---

### Frontend Components

#### [NEW] [frontend/package.json](file:///c:/Users/Admin/Desktop/agent-compilance-card-generator/frontend/package.json)
Modern frontend stack configurations matching React 19 + TypeScript + Vite + TailwindCSS.

#### [NEW] [frontend/tailwind.config.js](file:///c:/Users/Admin/Desktop/agent-compilance-card-generator/frontend/tailwind.config.js)
Tailwind color palette configuration tailored to the specific colors requested:
- Dark background (`#151515`)
- Dark sidebar (`#1F1F1F`)
- Sleek cards (`#2B2B2B`)
- Borders (`#404040`)
- Primary text (`#FAFAFA`)
- Accent triggers (`#C67C2E`)
- Alerts/Critical indicators (`#991B1B`)

#### [NEW] [frontend/src/pages/Dashboard.tsx](file:///c:/Users/Admin/Desktop/agent-compilance-card-generator/frontend/src/pages/Dashboard.tsx)
Overview dashboard with high-end telemetry charts (using Recharts), audit activity list, and summary cards.

#### [NEW] [frontend/src/pages/CardEditor.tsx](file:///c:/Users/Admin/Desktop/agent-compilance-card-generator/frontend/src/pages/CardEditor.tsx)
Drag-and-drop or file-upload panel for inputs (Agent Config, Tool Manifest, Runtime Trace) with direct visual compliance generation feedback.

#### [NEW] [frontend/src/pages/CardDetails.tsx](file:///c:/Users/Admin/Desktop/agent-compilance-card-generator/frontend/src/pages/CardDetails.tsx)
Detailed compliance card rendering showing:
- Interactive panels for each section (Scope, Operations, Decision Authority, etc.)
- Regulation checklists (EU AI Act, NIST AI RMF, ISO 42001)
- Version history timeline and **Visual Diff View**
- High-fidelity visual completeness scorecard

---

## Verification Plan

### Automated Tests
1. **Backend Unit & Integration Tests**:
   - Authentication system verification.
   - Parsing engine correctness (checks mapping functions).
   - Card revision diff engine.
   - Run tests command: `pytest backend/app/tests`
2. **Frontend Component Tests**:
   - Check input forms and diff component.
   - Run tests command: `npm run test` or `vite test`

### Manual Verification
1. **Docker Compose Launch**:
   - Execute `docker-compose up --build -d` to verify service integration (FastAPI + React SPA static bundle served via Nginx + PostgreSQL + Redis).
   - Access localhost:80 to perform end-to-end tests (upload trace/manifest files, view cards, trigger edits, review diffs, export PDF/JSON).
