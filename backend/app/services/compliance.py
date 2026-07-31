import re
import yaml
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple
from openai import OpenAI

from app.core.config import settings
from app.schemas.card import CardData, LLMInfo, ToolInfo
from app.schemas.regulation import RequirementCheck

# Set up OpenAI client (will be initialized if API key is present)
def get_openai_client() -> OpenAI | None:
    if settings.OPENAI_API_KEY:
        return OpenAI(api_key=settings.OPENAI_API_KEY)
    return None


def parse_input_to_dict(content: str) -> Dict[str, Any]:
    """Safely parse input string as JSON or YAML."""
    if not content:
        return {}
    content_stripped = content.strip()
    if not content_stripped:
        return {}
    
    # Try JSON
    if content_stripped.startswith("{") or content_stripped.startswith("["):
        try:
            return json.loads(content_stripped)
        except json.JSONDecodeError:
            pass
    
    # Try YAML
    try:
        parsed = yaml.safe_load(content_stripped)
        if isinstance(parsed, dict):
            return parsed
        elif isinstance(parsed, list):
            return {"list_data": parsed}
    except Exception:
        pass
    
    # Fallback to string container
    return {"raw_text": content}


class ComplianceEngine:
    @staticmethod
    def calculate_completeness(card_data: CardData) -> Tuple[float, List[str]]:
        """
        Calculates a completeness score and returns a list of missing or suspect fields.
        Completeness is evaluated on key fields of CardData.
        """
        fields_to_check = [
            ("purpose", card_data.purpose),
            ("scope", card_data.scope),
            ("llm_info.model_name", card_data.llm_info.model_name),
            ("llm_info.provider", card_data.llm_info.provider),
            ("prompt_info", card_data.prompt_info),
            ("operations", card_data.operations),
            ("data_access", card_data.data_access),
            ("decision_authority", card_data.decision_authority),
            ("human_oversight", card_data.human_oversight),
            ("incident_contact", card_data.incident_contact),
        ]
        
        missing_fields = []
        filled_count = 0
        placeholder_regex = re.compile(
            r"^(todo|placeholder|tbd|tbc|insert here|lorem ipsum|unknown|none|n/a|-)$", 
            re.IGNORECASE
        )
        
        for name, value in fields_to_check:
            if not value or str(value).strip() == "":
                missing_fields.append(f"Missing field: '{name}'")
            elif placeholder_regex.match(str(value).strip()):
                missing_fields.append(f"Placeholder detected in '{name}': '{value}'")
            else:
                filled_count += 1
                
        # List collections check
        if not card_data.tool_inventory:
            missing_fields.append("Tool Inventory is empty")
        else:
            filled_count += 0.5
            
        if not card_data.data_sources:
            missing_fields.append("Data Sources are empty")
        else:
            filled_count += 0.5
            
        total_checks = len(fields_to_check) + 1  # fields + 2 half checks
        completeness_score = round((filled_count / total_checks) * 100, 1)
        return min(completeness_score, 100.0), missing_fields

    @staticmethod
    def map_regulations(card_data: CardData) -> Dict[str, Dict[str, Any]]:
        """
        Maps the card fields to specific regulations (EU AI Act, NIST AI RMF, ISO 42001)
        and computes checklist results.
        """
        frameworks = {
            "EU AI Act Art.13": {
                "description": "Transparency and provision of information to users for high-risk AI systems.",
                "checks": [
                    {
                        "id": "EU-13.1",
                        "title": "Provider Information & Specifications",
                        "description": "System specifications including model type, version, provider, and parameters are declared.",
                        "status": "compliant" if card_data.llm_info.provider and card_data.llm_info.model_name else "non-compliant",
                        "evidence": f"LLM details provided: {card_data.llm_info.provider} / {card_data.llm_info.model_name}",
                        "remediation": "Provide model details (provider and version)."
                    },
                    {
                        "id": "EU-13.2",
                        "title": "Clear Purpose and Intended Use",
                        "description": "The system’s purpose, intended capabilities, and bounds of operations are clearly defined.",
                        "status": "compliant" if len(card_data.purpose) > 15 and len(card_data.scope) > 15 else "partially-compliant",
                        "evidence": f"Purpose: '{card_data.purpose[:40]}...', Scope: '{card_data.scope[:40]}...'",
                        "remediation": "Expand on purpose and boundaries of use to ensure complete user understanding."
                    },
                    {
                        "id": "EU-13.3",
                        "title": "Known Limitations & Failure Modes",
                        "description": "System limitations, known failure cases, or performance degradation conditions are logged.",
                        "status": "compliant" if card_data.known_limitations and len(card_data.known_limitations) > 0 else "non-compliant",
                        "evidence": f"Limitations documented: {', '.join(card_data.known_limitations) if card_data.known_limitations else 'None'}",
                        "remediation": "Define known boundaries or failure cases for user awareness."
                    }
                ]
            },
            "NIST AI RMF Govern": {
                "description": "NIST AI Risk Management Framework - Governance criteria.",
                "checks": [
                    {
                        "id": "NIST-GOV-1.1",
                        "title": "Decision Authority & Agency Limits",
                        "description": "Explicit declaration of the level of autonomy and decision-making authority.",
                        "status": "compliant" if len(card_data.decision_authority) > 10 else "non-compliant",
                        "evidence": f"Decision Authority: '{card_data.decision_authority}'",
                        "remediation": "Document boundaries of the agent's delegation and approval thresholds."
                    },
                    {
                        "id": "NIST-GOV-1.2",
                        "title": "Human Oversight Mechanism",
                        "description": "Established mechanisms for human-in-the-loop approvals, auditing, or override capabilities.",
                        "status": "compliant" if "human" in card_data.human_oversight.lower() or "approval" in card_data.human_oversight.lower() else "partially-compliant",
                        "evidence": f"Human Oversight: '{card_data.human_oversight}'",
                        "remediation": "Define oversight methods (e.g. thresholds, manual review, post-audit)."
                    },
                    {
                        "id": "NIST-GOV-1.3",
                        "title": "Incident & Accountability Response",
                        "description": "Clearly defined emergency contact or rollback triggers for anomalous behavior.",
                        "status": "compliant" if card_data.incident_contact and "@" in card_data.incident_contact else "non-compliant",
                        "evidence": f"Incident contact: {card_data.incident_contact}",
                        "remediation": "Provide a valid security contact email/phone for compliance alerts."
                    }
                ]
            },
            "ISO/IEC 42001": {
                "description": "Standard for Artificial Intelligence Management Systems.",
                "checks": [
                    {
                        "id": "ISO-42001-A.1",
                        "title": "Tool Inventory and Access Policies",
                        "description": "Documented capabilities, plugins, or system tool integration lists.",
                        "status": "compliant" if len(card_data.tool_inventory) > 0 else "non-compliant",
                        "evidence": f"Found {len(card_data.tool_inventory)} tool configurations.",
                        "remediation": "Document all API tools and extensions the agent is permitted to execute."
                    },
                    {
                        "id": "ISO-42001-A.2",
                        "title": "Data Resource Governance",
                        "description": "Information regarding input data sources and database systems accessed.",
                        "status": "compliant" if len(card_data.data_sources) > 0 else "non-compliant",
                        "evidence": f"Data Sources: {', '.join(card_data.data_sources) if card_data.data_sources else 'None'}",
                        "remediation": "Add data catalogs and third-party data inputs accessed by the model."
                    },
                    {
                        "id": "ISO-42001-A.3",
                        "title": "Robustness and Risk Control",
                        "description": "Assessment of systemic risk and potential harm levels.",
                        "status": "compliant" if card_data.risk_classification in ["low", "medium", "high", "critical"] else "non-compliant",
                        "evidence": f"Risk level assessed as: {card_data.risk_classification.upper()}",
                        "remediation": "Verify and align risk categorization to organization policies."
                    }
                ]
            }
        }
        
        # Calculate summary status for each framework
        for fw_name, fw_info in frameworks.items():
            statuses = [check["status"] for check in fw_info["checks"]]
            if "non-compliant" in statuses:
                fw_info["status"] = "non-compliant"
            elif "partially-compliant" in statuses:
                fw_info["status"] = "partially-compliant"
            else:
                fw_info["status"] = "compliant"
                
        return frameworks

    @classmethod
    def generate_card_rule_based(cls, config: Dict[str, Any], tool_manifest: Dict[str, Any], runtime_trace: str) -> CardData:
        """Robust rule-based parser as a fallback or default when OpenAI is unavailable."""
        
        # 1. Parse LLM Info
        provider = "Unknown"
        model_name = "unknown-model"
        temperature = 0.7
        
        # Look in config
        if isinstance(config, dict):
            # Check model settings
            for key in ["model", "model_name", "llm", "llm_model"]:
                if key in config and isinstance(config[key], str):
                    model_name = config[key]
            
            # Check provider
            for key in ["provider", "platform", "vendor", "llm_provider"]:
                if key in config and isinstance(config[key], str):
                    provider = config[key]
            
            if "temperature" in config:
                try:
                    temperature = float(config["temperature"])
                except Exception:
                    pass
                    
        # Trace scanning for model info
        if model_name == "unknown-model" and runtime_trace:
            model_matches = re.findall(r"(gpt-4o-mini|gpt-4o|gpt-4|claude-3-5-sonnet|claude-3-opus|llama3|gemini-1\.5-pro)", runtime_trace, re.IGNORECASE)
            if model_matches:
                model_name = model_matches[0].lower()
                if "gpt" in model_name:
                    provider = "OpenAI"
                elif "claude" in model_name:
                    provider = "Anthropic"
                elif "llama" in model_name:
                    provider = "Meta"
                elif "gemini" in model_name:
                    provider = "Google"

        # Defaults
        if provider == "Unknown" and "gpt" in model_name.lower():
            provider = "OpenAI"
        elif provider == "Unknown" and "claude" in model_name.lower():
            provider = "Anthropic"

        llm_info = LLMInfo(
            provider=provider,
            model_name=model_name,
            version="latest",
            temperature=temperature
        )

        # 2. Extract Tool Inventory
        tool_inventory: List[ToolInfo] = []
        
        # Parse from tool manifest
        tools_list = []
        if isinstance(tool_manifest, dict):
            if "tools" in tool_manifest and isinstance(tool_manifest["tools"], list):
                tools_list = tool_manifest["tools"]
            elif "functions" in tool_manifest and isinstance(tool_manifest["functions"], list):
                tools_list = tool_manifest["functions"]
            else:
                # check if the dictionary keys are themselves tools
                for k, v in tool_manifest.items():
                    if isinstance(v, dict) and ("description" in v or "name" in v):
                        tools_list.append(v)
        elif isinstance(tool_manifest, list):
            tools_list = tool_manifest

        for t in tools_list:
            t_name = "unknown_tool"
            t_desc = "No description provided."
            t_perms = []
            
            if isinstance(t, dict):
                t_name = t.get("name") or t.get("id") or t_name
                t_desc = t.get("description") or t.get("desc") or t_desc
                t_perms = t.get("permissions") or t.get("scopes") or []
                if isinstance(t_perms, str):
                    t_perms = [t_perms]
            elif isinstance(t, str):
                t_name = t
                
            # Deduplicate
            if t_name not in [x.name for x in tool_inventory]:
                # Gauge impact level based on write access keywords
                impact = "low"
                if any(x in t_name.lower() or x in t_desc.lower() for x in ["delete", "remove", "write", "update", "execute", "post", "publish", "send"]):
                    impact = "medium"
                if any(x in t_name.lower() or x in t_desc.lower() for x in ["db_drop", "destroy", "root", "admin", "truncate", "delete_database", "drop_table"]):
                    impact = "high"
                    
                tool_inventory.append(ToolInfo(
                    name=t_name,
                    description=t_desc,
                    permissions=list(t_perms),
                    impact_level=impact
                ))

        # 3. Parse fields from config, or use fallbacks
        purpose = "Not defined."
        scope = "Not defined."
        prompt_info = "Not defined."
        operations = "Executes workflows."
        data_access = "Determined by tools."
        data_sources = []
        decision_authority = "Supervised"
        human_oversight = "Human-in-the-loop review."
        risk_classification = "low"
        known_limitations = []
        incident_contact = "security-alerts@company.internal"
        
        if isinstance(config, dict):
            purpose = config.get("purpose") or config.get("description") or config.get("goal") or purpose
            scope = config.get("scope") or config.get("allowed_domains") or scope
            prompt_info = config.get("system_prompt") or config.get("prompt") or config.get("instructions") or prompt_info
            operations = config.get("operations") or config.get("tasks") or operations
            data_access = config.get("data_access") or config.get("database_access") or data_access
            incident_contact = config.get("contact") or config.get("owner_email") or config.get("incident_contact") or incident_contact
            
            # Data sources list
            d_sources = config.get("data_sources") or config.get("databases") or []
            if isinstance(d_sources, str):
                data_sources = [d_sources]
            elif isinstance(d_sources, list):
                data_sources = [str(x) for x in d_sources]
                
            # Decision authority
            if "autonomy" in config or "decision_authority" in config:
                decision_authority = config.get("autonomy") or config.get("decision_authority")
            else:
                if config.get("human_in_the_loop") is False or config.get("autonomous") is True:
                    decision_authority = "Autonomous"
                else:
                    decision_authority = "Supervised Autonomy"
                    
            # Human oversight
            human_oversight = config.get("human_oversight") or config.get("oversight") or human_oversight
            
            # Limitations
            limitations = config.get("limitations") or config.get("known_issues") or []
            if isinstance(limitations, str):
                known_limitations = [limitations]
            elif isinstance(limitations, list):
                known_limitations = [str(x) for x in limitations]

        # Scan trace for data sources, authority and limitations
        if runtime_trace:
            # Look for DB access patterns
            db_matches = re.findall(r"(postgresql|mongodb|mysql|redis|sqlite|oracle|s3|elasticsearch)", runtime_trace, re.IGNORECASE)
            for db in db_matches:
                db_l = db.lower()
                if db_l not in data_sources:
                    data_sources.append(db_l)
            
            # Check for error patterns
            error_matches = re.findall(r"(exception|error|timeout|rate limit|failed|unauthorized)", runtime_trace, re.IGNORECASE)
            if error_matches and not known_limitations:
                known_limitations.append("Susceptible to transient API timeouts or rate limits.")
                
            # Check for human approval events
            if re.search(r"(human_approve|user_confirm|approved by human|wait_for_user)", runtime_trace, re.IGNORECASE):
                decision_authority = "Supervised"
                human_oversight = "Mandatory human sign-off before safety-critical tool executions."

        # Risk Classification heuristics
        # Critical: handles root db, write commands autonomously
        # High: writes/updates DB or third-party APIs autonomously
        # Medium: write access but supervised, or read-only autonomous
        # Low: read-only supervised
        has_write = len([t for t in tool_inventory if t.impact_level in ["medium", "high"]]) > 0
        is_autonomous = "autonomous" in str(decision_authority).lower()
        
        if has_write and is_autonomous:
            risk_classification = "high"
            # Upgrade to critical if there are high impact tools
            if len([t for t in tool_inventory if t.impact_level == "high"]) > 0:
                risk_classification = "critical"
        elif has_write or is_autonomous:
            risk_classification = "medium"
        else:
            risk_classification = "low"

        # Create CardData object
        card_data = CardData(
            purpose=str(purpose),
            scope=str(scope),
            llm_info=llm_info,
            prompt_info=str(prompt_info),
            tool_inventory=tool_inventory,
            operations=str(operations),
            data_access=str(data_access),
            data_sources=data_sources if data_sources else ["Configuration Context"],
            decision_authority=str(decision_authority),
            human_oversight=str(human_oversight),
            risk_classification=risk_classification,
            known_limitations=known_limitations if known_limitations else ["No documented limitations."],
            incident_contact=str(incident_contact),
            audit_metadata={
                "engine": "Rule-Based Compliance Engine v1.0",
                "extracted_at": datetime.now(timezone.utc).isoformat()
            },
            timestamp=datetime.now(timezone.utc),
            version="1.0.0",
            confidence_score=0.75 if runtime_trace else 0.60
        )
        
        return card_data

    @classmethod
    def generate_card(cls, config_str: str, tool_manifest_str: str, runtime_trace_str: str) -> CardData:
        """
        Runs the Compliance Generator. 
        Tries to use OpenAI if key is present; otherwise falls back to Rule-Based engine.
        """
        config = parse_input_to_dict(config_str)
        tool_manifest = parse_input_to_dict(tool_manifest_str)
        runtime_trace = runtime_trace_str or ""
        
        client = get_openai_client()
        if not client:
            # Fallback
            return cls.generate_card_rule_based(config, tool_manifest, runtime_trace)
            
        try:
            # Let's prompt OpenAI
            prompt = f"""
            Analyze the following three inputs from an AI Agent system deployment and extract a structured compliance profile mapping directly to the target Pydantic schema.
            
            1. Agent Configuration File:
            ```
            {config_str}
            ```
            
            2. Tool Manifest File:
            ```
            {tool_manifest_str}
            ```
            
            3. Execution/Runtime Trace Logs:
            ```
            {runtime_trace_str}
            ```
            
            Extract and populate all fields for the Agent Compliance Card:
            - purpose (broad context of what the agent is created to do)
            - scope (boundaries, guardrails, and allowed operations)
            - llm_info (provider e.g. OpenAI/Anthropic/etc., model_name e.g. gpt-4o, version, temperature)
            - prompt_info (summary of the system instructions and guidelines)
            - tool_inventory (list of tools, their descriptions, permissions, and impact levels e.g. low/medium/high)
            - operations (how it behaves operationally)
            - data_access (what levels of read/write access it has to external databases or APIs)
            - data_sources (where it pulls data from)
            - decision_authority (level of decision authority e.g. autonomous, supervised, human-in-the-loop)
            - human_oversight (what human oversight controls exist)
            - risk_classification (low, medium, high, critical)
            - known_limitations (known issues, rate limits, error points)
            - incident_contact (valid point of contact email)
            
            Provide a clean JSON response that matches the schema of:
            {{
                "purpose": "string",
                "scope": "string",
                "llm_info": {{
                    "provider": "string",
                    "model_name": "string",
                    "version": "string",
                    "temperature": float
                }},
                "prompt_info": "string",
                "tool_inventory": [
                    {{
                        "name": "string",
                        "description": "string",
                        "permissions": ["string"],
                        "impact_level": "low/medium/high"
                    }}
                ],
                "operations": "string",
                "data_access": "string",
                "data_sources": ["string"],
                "decision_authority": "string",
                "human_oversight": "string",
                "risk_classification": "low/medium/high/critical",
                "known_limitations": ["string"],
                "incident_contact": "string"
            }}
            """
            
            # Using new client syntax (v1.0.0+)
            # Request JSON mode to guarantee compliance
            response = client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a professional AI Governance and Risk Auditor. Your job is to analyze agent architectures and generate precise, factual compliance logs in structured JSON format. Avoid placeholder text, TBDs, or hallucinated facts. Evaluate based strictly on the provided config, manifest, and runtime traces."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                timeout=30.0
            )
            
            result_json = json.loads(response.choices[0].message.content)
            
            # Map tools correctly
            tools = [
                ToolInfo(
                    name=t.get("name", "unknown_tool"),
                    description=t.get("description", ""),
                    permissions=t.get("permissions", []),
                    impact_level=t.get("impact_level", "low")
                ) for t in result_json.get("tool_inventory", [])
            ]
            
            llm_info = LLMInfo(
                provider=result_json.get("llm_info", {}).get("provider", "OpenAI"),
                model_name=result_json.get("llm_info", {}).get("model_name", "gpt-4o-mini"),
                version=result_json.get("llm_info", {}).get("version", "latest"),
                temperature=result_json.get("llm_info", {}).get("temperature", 0.7)
            )
            
            card_data = CardData(
                purpose=result_json.get("purpose", ""),
                scope=result_json.get("scope", ""),
                llm_info=llm_info,
                prompt_info=result_json.get("prompt_info", ""),
                tool_inventory=tools,
                operations=result_json.get("operations", ""),
                data_access=result_json.get("data_access", ""),
                data_sources=result_json.get("data_sources", []),
                decision_authority=result_json.get("decision_authority", ""),
                human_oversight=result_json.get("human_oversight", ""),
                risk_classification=result_json.get("risk_classification", "low"),
                known_limitations=result_json.get("known_limitations", []),
                incident_contact=result_json.get("incident_contact", "security-alerts@company.internal"),
                audit_metadata={
                    "engine": "OpenAI LLM Compliance Engine v1.0",
                    "model": settings.OPENAI_MODEL,
                    "extracted_at": datetime.now(timezone.utc).isoformat()
                },
                timestamp=datetime.now(timezone.utc),
                version="1.0.0",
                confidence_score=0.95
            )
            return card_data
            
        except Exception:
            # Fallback if OpenAI call fails
            return cls.generate_card_rule_based(config, tool_manifest, runtime_trace)
