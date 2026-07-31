from typing import Any, Dict, List
from app.schemas.card import CardData

class DiffEngine:
    @staticmethod
    def diff_cards(c1: CardData, c2: CardData) -> Dict[str, Any]:
        """
        Computes the difference between two card versions.
        Detects if critical fields changed that require compliance reassessment.
        """
        diff = {}
        reassessment_triggers = []
        
        # 1. Compare Simple string/numeric fields
        simple_fields = [
            ("purpose", "Purpose"),
            ("scope", "Scope"),
            ("operations", "Operations"),
            ("data_access", "Data Access"),
            ("decision_authority", "Decision Authority"),
            ("risk_classification", "Risk Classification"),
            ("incident_contact", "Incident Contact"),
            ("prompt_info", "Prompt Info")
        ]
        
        for field, label in simple_fields:
            v1 = getattr(c1, field, "")
            v2 = getattr(c2, field, "")
            if v1 != v2:
                diff[field] = {
                    "label": label,
                    "v1": v1,
                    "v2": v2,
                    "changed": True
                }
                # Check for critical triggers
                if field in ["data_access", "decision_authority", "risk_classification"]:
                    reassessment_triggers.append(label)

        # 2. Compare LLM Info
        llm_changed = False
        llm_diff = {}
        if c1.llm_info.provider != c2.llm_info.provider:
            llm_diff["provider"] = {"v1": c1.llm_info.provider, "v2": c2.llm_info.provider}
            llm_changed = True
        if c1.llm_info.model_name != c2.llm_info.model_name:
            llm_diff["model_name"] = {"v1": c1.llm_info.model_name, "v2": c2.llm_info.model_name}
            llm_changed = True
        if c1.llm_info.temperature != c2.llm_info.temperature:
            llm_diff["temperature"] = {"v1": c1.llm_info.temperature, "v2": c2.llm_info.temperature}
            
        if llm_changed:
            reassessment_triggers.append("LLM / Model Settings")
            diff["llm_info"] = {
                "label": "LLM Config",
                "changed": True,
                "details": llm_diff
            }
        elif llm_diff:
            diff["llm_info"] = {
                "label": "LLM Config",
                "changed": False,
                "details": llm_diff
            }

        # 3. Compare Tools (Inventory)
        t1_names = {t.name: t for t in c1.tool_inventory}
        t2_names = {t.name: t for t in c2.tool_inventory}
        
        added_tools = []
        removed_tools = []
        modified_tools = {}
        
        for name, t in t2_names.items():
            if name not in t1_names:
                added_tools.append({"name": name, "description": t.description, "impact_level": t.impact_level})
            else:
                # Compare fields of the tool
                t1 = t1_names[name]
                t_diff = {}
                if t1.description != t.description:
                    t_diff["description"] = {"v1": t1.description, "v2": t.description}
                if t1.permissions != t.permissions:
                    t_diff["permissions"] = {"v1": t1.permissions, "v2": t.permissions}
                if t1.impact_level != t.impact_level:
                    t_diff["impact_level"] = {"v1": t1.impact_level, "v2": t.impact_level}
                if t_diff:
                    modified_tools[name] = t_diff
                    
        for name, t in t1_names.items():
            if name not in t2_names:
                removed_tools.append({"name": name, "description": t.description, "impact_level": t.impact_level})
                
        if added_tools or removed_tools or modified_tools:
            reassessment_triggers.append("Tool Inventory")
            diff["tools"] = {
                "label": "Tools Inventory",
                "changed": True,
                "added": added_tools,
                "removed": removed_tools,
                "modified": modified_tools
            }

        # 4. Compare Data Sources
        ds1 = set(c1.data_sources)
        ds2 = set(c2.data_sources)
        
        added_ds = list(ds2 - ds1)
        removed_ds = list(ds1 - ds2)
        
        if added_ds or removed_ds:
            reassessment_triggers.append("Data Sources")
            diff["data_sources"] = {
                "label": "Data Sources",
                "changed": True,
                "added": added_ds,
                "removed": removed_ds
            }

        # Determine if reassessment is required
        # Automatic reassessment when LLM, tools, permissions, decision authority, data sources or risk change
        reassessment_required = len(reassessment_triggers) > 0
        
        return {
            "has_changes": len(diff) > 0,
            "reassessment_required": reassessment_required,
            "reassessment_reasons": reassessment_triggers,
            "changes": diff
        }
