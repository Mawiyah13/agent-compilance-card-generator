# Agent Compliance Card Generator

An enterprise-grade AI Governance and Compliance management platform. It ingests AI agent configurations, tool manifests, and runtime trace execution logs to generate **Agent Compliance Cards** detailing operations, risk profiles, human oversight models, and automatic regulation checks mapped to global standards.

## Project Architecture & Core Features

- **Automatic Regulation Mapping**: Evaluates inputs against EU AI Act Art.13, NIST AI RMF Govern, and ISO/IEC 42001.
- **Completeness Checker**: Detects missing or suspect fields and calculates a compliance score.
- **Version Control & Diffing**: Tracks revisions, compares versions, and triggers version bumps for material changes.
- **Export Support**: Download PDF reports and JSON snapshots of card versions.
- **Auth + RBAC**: JWT access/refresh flows, and audit log access restricted to admin/auditor roles.

## Directory Structure

```
├── backend/                  # FastAPI application and Alembic migrations
│   ├── app/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   └── alembic/
├── frontend/                 # React SPA and Nginx hosting config
├── terraform/                # AWS ECS, RDS, Redis, VPC, and ALB definitions
├── docker-compose.yml        # Local development stack
└── README.md
```

## Quick Start (Docker Compose)

Bring up the full stack locally:

```bash
copy .env.example .env
docker compose up --build -d
```

- Frontend: `http://localhost:80`
- API docs: `http://localhost:8000/api/v1/docs`
- Health: `http://localhost:8000/health`

## Backend Startup

```bash
cd backend
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

## Health Endpoints

- `GET /health` — DB + Redis
- `GET /health/liveness` — process alive
- `GET /health/readiness` — readiness after DB/Redis available

## Database Migrations

```bash
cd backend
venv\Scripts\python.exe -m alembic upgrade head
```

The backend can also auto-bootstrap tables via SQLAlchemy if migrations are not run.

## Frontend Startup

```bash
cd frontend
npm install
npm run dev
```

## Authentication

- Register: `POST /api/v1/auth/register`
- Login: `POST /api/v1/auth/login`
- Refresh: `POST /api/v1/auth/refresh?refresh_token=...`
- Current user: `GET /api/v1/auth/me`

## Export Endpoints

- `GET /api/v1/cards/{card_id}/export/pdf`
- `GET /api/v1/cards/{card_id}/export/json`

## Testing

From the repo root:

```bash
backend\venv\Scripts\python.exe -m pytest -q
```

## Terraform

Provision AWS infrastructure for ECS, RDS, Redis, IAM, and ALB.

```bash
cd terraform
terraform init
terraform plan -var='aws_region=us-east-1' -var='db_password=YOUR_DB_PASSWORD' -var='openai_api_key=YOUR_OPENAI_API_KEY' -var='secret_key=YOUR_JWT_SECRET' -var='ecr_backend_url=YOUR_BACKEND_ECR' -var='ecr_frontend_url=YOUR_FRONTEND_ECR'
```

Make sure AWS permissions include ECS, RDS, ElastiCache, IAM, and ALB actions.
