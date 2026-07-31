from app.services.compliance import ComplianceEngine
from app.schemas.card import CardData, LLMInfo, ToolInfo

def test_rule_based_parser_simple():
    config = {
        "purpose": "A test agent designed to help developers create cards.",
        "scope": "Within localhost workspace directory.",
        "model": "gpt-4o-mini",
        "provider": "OpenAI",
        "human_in_the_loop": True,
        "contact": "dev-team@company.internal",
        "data_sources": ["postgresql", "s3"]
    }
    
    tool_manifest = {
        "tools": [
            {
                "name": "read_file",
                "description": "Read file from disk.",
                "permissions": ["file_read"]
            },
            {
                "name": "delete_database",
                "description": "Deletes the entire postgres database.",
                "permissions": ["db_admin"]
            }
        ]
    }
    
    trace = "Successfully started. Invoking read_file... wait_for_user approval before delete_database. Confirmed."
    
    card = ComplianceEngine.generate_card_rule_based(config, tool_manifest, trace)
    
    assert card.purpose == "A test agent designed to help developers create cards."
    assert card.scope == "Within localhost workspace directory."
    assert card.llm_info.provider == "OpenAI"
    assert card.llm_info.model_name == "gpt-4o-mini"
    assert card.incident_contact == "dev-team@company.internal"
    assert "postgresql" in card.data_sources
    assert "s3" in card.data_sources
    
    assert len(card.tool_inventory) == 2
    assert card.tool_inventory[0].name == "read_file"
    assert card.tool_inventory[1].impact_level == "high"  # due to 'delete_database'

def test_completeness_checker():
    # Complete card
    card = CardData(
        purpose="Help developers test compliance",
        scope="Workspace sandbox only",
        llm_info=LLMInfo(provider="OpenAI", model_name="gpt-4o", version="latest", temperature=0.7),
        prompt_info="Be a helpful assistant",
        tool_inventory=[ToolInfo(name="read", description="read data")],
        operations="Processes system files",
        data_access="Read-only permissions",
        data_sources=["local_files"],
        decision_authority="Supervised",
        human_oversight="Approval on write operations",
        risk_classification="low",
        known_limitations=["None"],
        incident_contact="test@company.com",
        audit_metadata={},
        version="1.0.0",
        confidence_score=0.9
    )
    
    score, missing = ComplianceEngine.calculate_completeness(card)
    assert score == 100.0
    assert len(missing) == 0

    # Incomplete card
    incomplete_card = CardData(
        purpose="",
        scope="",
        llm_info=LLMInfo(provider="", model_name="unknown-model", version="latest", temperature=0.7),
        prompt_info="",
        tool_inventory=[],
        operations="Incomplete operational description",
        data_access="",
        data_sources=[],
        decision_authority="Autonomous",
        human_oversight="none",
        risk_classification="low",
        known_limitations=[],
        incident_contact="",
        audit_metadata={},
        version="1.0.0",
        confidence_score=0.5
    )
    score, missing = ComplianceEngine.calculate_completeness(incomplete_card)
    assert score < 50.0
    assert len(missing) > 0

def test_regulation_mappings():
    card = CardData(
        purpose="Generate agent compliance cards",
        scope="Workspace directory",
        llm_info=LLMInfo(provider="OpenAI", model_name="gpt-4o", version="latest", temperature=0.7),
        prompt_info="Analyze inputs and write cards",
        tool_inventory=[ToolInfo(name="write_file", description="write files to folder")],
        operations="Parses JSON and generates YAML outputs",
        data_access="Write access in workspace directory",
        data_sources=["local_files"],
        decision_authority="Autonomous",
        human_oversight="None",
        risk_classification="medium",
        known_limitations=["No trace available"],
        incident_contact="alerts@company.internal",
        audit_metadata={},
        version="1.0.0",
        confidence_score=0.85
    )
    
    mappings = ComplianceEngine.map_regulations(card)
    
    assert "EU AI Act Art.13" in mappings
    assert "NIST AI RMF Govern" in mappings
    assert "ISO/IEC 42001" in mappings
    
    assert mappings["EU AI Act Art.13"]["status"] in ["compliant", "partially-compliant", "non-compliant"]
    assert mappings["NIST AI RMF Govern"]["status"] in ["compliant", "partially-compliant", "non-compliant"]
