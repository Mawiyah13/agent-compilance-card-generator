from app.services.diff import DiffEngine
from app.schemas.card import CardData, LLMInfo, ToolInfo

def test_diff_engine_no_changes():
    c1 = CardData(
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
    
    # Exact copy
    c2 = c1.model_copy()
    
    diff_res = DiffEngine.diff_cards(c1, c2)
    assert diff_res["has_changes"] is False
    assert diff_res["reassessment_required"] is False
    assert len(diff_res["changes"]) == 0

def test_diff_engine_reassessment_triggers():
    c1 = CardData(
        purpose="Help developers test compliance",
        scope="Workspace sandbox only",
        llm_info=LLMInfo(provider="OpenAI", model_name="gpt-4o", version="latest", temperature=0.7),
        prompt_info="Be a helpful assistant",
        tool_inventory=[ToolInfo(name="read", description="read data", permissions=["read"])],
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
    
    # Change model to Claude (should trigger reassessment)
    c2 = c1.model_copy()
    c2.llm_info = LLMInfo(provider="Anthropic", model_name="claude-3-5-sonnet", version="latest", temperature=0.7)
    
    # Add high impact tool (should trigger reassessment)
    c2.tool_inventory = [
        ToolInfo(name="read", description="read data", permissions=["read"]),
        ToolInfo(name="destroy_db", description="Deletes database", permissions=["admin"], impact_level="high")
    ]
    
    # Change risk level
    c2.risk_classification = "high"
    
    diff_res = DiffEngine.diff_cards(c1, c2)
    assert diff_res["has_changes"] is True
    assert diff_res["reassessment_required"] is True
    assert "LLM / Model Settings" in diff_res["reassessment_reasons"]
    assert "Tool Inventory" in diff_res["reassessment_reasons"]
    assert "Risk Classification" in diff_res["reassessment_reasons"]
    
    changes = diff_res["changes"]
    assert "llm_info" in changes
    assert "tools" in changes
    assert "risk_classification" in changes
    
    # Verify tool added detail
    tools_diff = changes["tools"]
    assert len(tools_diff["added"]) == 1
    assert tools_diff["added"][0]["name"] == "destroy_db"
