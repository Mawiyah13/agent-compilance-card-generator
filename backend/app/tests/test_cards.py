import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.schemas.card import CardData, LLMInfo, ToolInfo

client = TestClient(app)


def create_test_user():
    email = f"card-user-{uuid.uuid4().hex[:8]}@example.com"
    password = "TestPass123"
    register_response = client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={"email": email, "password": password, "role": "developer"}
    )
    assert register_response.status_code == 201

    login_response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data={"username": email, "password": password}
    )
    assert login_response.status_code == 200
    token_data = login_response.json()
    return token_data["access_token"]


def test_update_compliance_card_creates_new_version():
    token = create_test_user()
    headers = {"Authorization": f"Bearer {token}"}

    create_response = client.post(
        f"{settings.API_V1_STR}/cards",
        headers=headers,
        data={
            "name": "Original Card",
            "config_text": "{\"purpose\": \"Original purpose\"}",
            "tool_manifest_text": "{\"tools\": []}",
            "runtime_trace_text": "start"
        }
    )
    assert create_response.status_code == 201
    created = create_response.json()
    card_id = created["id"]
    original_version_id = created["current_version"]["id"]

    update_response = client.put(
        f"{settings.API_V1_STR}/cards/{card_id}",
        headers=headers,
        data={
            "name": "Original Card v2",
            "config_text": "{\"purpose\": \"Edited purpose\"}"
        }
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["name"] == "Original Card v2"
    assert updated["current_version"]["id"] != original_version_id
    assert updated["current_version"]["version"] != "1.0.0"

    versions_response = client.get(
        f"{settings.API_V1_STR}/cards/{card_id}/versions",
        headers=headers
    )
    assert versions_response.status_code == 200
    versions = versions_response.json()
    assert len(versions) >= 2
    version_ids = {version["id"] for version in versions}
    assert original_version_id in version_ids
    assert updated["current_version"]["id"] in version_ids


def test_generate_compliance_pdf_long_remediation_wraps():
    card_data = CardData(
        purpose="Test long remediation wrapping",
        scope="Full production audit",
        llm_info=LLMInfo(provider="OpenAI", model_name="gpt-4o", version="2026-07", temperature=0.7),
        prompt_info="Summarize operations and compliance.",
        tool_inventory=[ToolInfo(name="db_query", description="Query internal DB for records", permissions=["read_db"], impact_level="low")],
        operations="Reads records and generates summaries.",
        data_access="Read-only access to audit database.",
        data_sources=["postgresql", "s3"],
        decision_authority="Supervised",
        human_oversight="Review before approval",
        risk_classification="low",
        known_limitations=["Cannot access external services"],
        incident_contact="security@company.com",
        audit_metadata={"engine": "Rule-Based Compliance Engine v1.0", "extracted_at": "2026-07-31T00:00:00Z"},
        version="1.0.0",
        confidence_score=0.9
    )
    from app.services.pdf_generator import generate_compliance_pdf

    long_remediation = (
        "This remediation text is intentionally long to validate wrapping behavior in the generated PDF. "
        "It includes multiple sentences and a lengthy description of steps to remediate the issue, such as updating controls, "
        "documenting processes, and verifying outputs. The text should not be truncated or overflow the cell boundary."
    )
    mappings = {
        "EU AI Act Art.13": {
            "description": "Transparency check for model disclosure.",
            "checks": [
                {
                    "id": "EU-13.1",
                    "title": "Provider Information & Specifications",
                    "status": "compliant",
                    "remediation": long_remediation,
                }
            ]
        }
    }

    pdf_bytes = generate_compliance_pdf("Long Remediation Card", card_data, 92.0, mappings)
    assert isinstance(pdf_bytes, (bytes, bytearray))
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 1000
