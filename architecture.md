# System Architecture & API Specifications

This document outlines the system architecture, ER database diagram, and core REST API specifications for the Agent Compliance Card Generator.

## Architecture Block Diagram

```mermaid
graph TD
    User[Web Client / React SPA] -->|HTTPS Requests| ALB[AWS Application Load Balancer]
    ALB -->|Root Path /| Frontend[React 19 Fargate Containers]
    ALB -->|API Path /api/*| Backend[FastAPI Fargate Containers]
    Backend -->|Async Connect| Postgres[(RDS PostgreSQL)]
    Backend -->|Caching & Rate Limiting| Redis[(ElastiCache Redis)]
    Backend -->|Analysis| OpenAI[OpenAI API / LLM Fallback]
```

## Entity Relationship (ER) Diagram

```mermaid
erDiagram
    USERS {
        uuid id PK
        string email
        string hashed_password
        string role
        boolean is_active
        datetime created_at
        datetime updated_at
    }
    COMPLIANCE_CARDS {
        uuid id PK
        string name
        uuid current_version_id FK
        uuid created_by_id FK
        datetime created_at
        datetime updated_at
    }
    CARD_VERSIONS {
        uuid id PK
        uuid card_id FK
        string version
        json config_input
        json tool_manifest_input
        text runtime_trace_input
        json card_data
        float completeness_score
        string risk_classification
        float confidence_score
        uuid created_by_id FK
        datetime created_at
    }
    REGULATION_MAPPINGS {
        uuid id PK
        uuid version_id FK
        string framework
        string status
        json details
    }
    AUDIT_LOGS {
        uuid id PK
        uuid user_id FK
        string action
        json details
        string ip_address
        datetime timestamp
    }

    USERS ||--o{ COMPLIANCE_CARDS : "creates"
    USERS ||--o{ CARD_VERSIONS : "versions"
    COMPLIANCE_CARDS ||--o{ CARD_VERSIONS : "has"
    CARD_VERSIONS ||--o{ REGULATION_MAPPINGS : "maps"
    USERS ||--o{ AUDIT_LOGS : "triggers"
```

## REST API Specification (v1)

### Authentication
- `POST /api/v1/auth/register`: Create a new developer or auditor user profile.
- `POST /api/v1/auth/login`: Authenticate email and password, returning JWT access and refresh tokens.
- `POST /api/v1/auth/refresh`: Refresh an expired access token.
- `GET /api/v1/auth/me`: Fetch profile information of the currently authenticated user.

### Compliance Cards
- `GET /api/v1/cards/`: List compliance cards with filters for search query (`search`) and risk level (`risk`).
- `POST /api/v1/cards/`: Compile inputs (config, tool manifest, trace logs) and generate a new compliance card.
- `GET /api/v1/cards/{card_id}`: Retrieve card details.
- `PUT /api/v1/cards/{card_id}`: Upload updated inputs, triggering a semver bump and recalculation.
- `GET /api/v1/cards/{card_id}/versions`: Get the list of all historical versions for the card.
- `GET /api/v1/cards/{card_id}/diff`: Calculate semantic differences between two card versions.
- `GET /api/v1/cards/{card_id}/export/pdf`: Stream a professional PDF report.
- `GET /api/v1/cards/{card_id}/export/json`: Download card specifications in structured JSON.

### Auditing
- `GET /api/v1/audit/`: List system audit logs (auditors and administrators only).
