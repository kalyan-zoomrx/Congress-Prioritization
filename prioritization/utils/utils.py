import os
import json
import pandas as pd
import json
import pandas as pd
from typing import Any, Dict
from functools import lru_cache
from prioritization.utils.logger import get_logger

logger = get_logger("Utils")


@lru_cache(maxsize=128)
def get_prompt(prompt_name: str):
    try:
        with open(f"prioritization/prompts/{prompt_name}.txt", "r", encoding="utf-8") as f:
            prompt = f.read()
            logger.info(f"Prompt: {prompt_name} read successfully")
            return prompt

    except FileNotFoundError:
        logger.error(f"Prompt: {prompt_name} not found")
        raise
    except Exception as e:
        logger.error(f"Error reading prompt {prompt_name}: {str(e)}")
        raise


def normalize_json_to_dataframe(json_object: Dict[str, Any] | list[Dict[str, Any]]) -> pd.DataFrame:
    """
    Converts an in-memory JSON object to CSV with flattened keys.
    Treats relevance_rule and priority_rules as separate rows.
    Converts lists to comma-separated strings.
    """

    def _flatten(data: Dict[str, Any], parent_key: str = "") -> Dict[str, Any]:
        items = {}

        for key, value in data.items():
            new_key = f"{parent_key}.{key}" if parent_key else key

            if isinstance(value, dict):
                items.update(_flatten(value, new_key))

            elif isinstance(value, list):
                # Convert list to comma-separated string
                if all(isinstance(item, (str, int, float, bool)) for item in value):
                    items[new_key] = ", ".join(str(item) for item in value)
                else:
                    # For nested structures, use JSON
                    items[new_key] = json.dumps(value, ensure_ascii=False)

            else:
                items[new_key] = value

        return items

    try:
        rows = []
        
        if isinstance(json_object, dict):
            # Check if this is the specific structure with relevance_rule and priority_rules
            if "relevance_rule" in json_object and "priority_rules" in json_object:
                # Add relevance_rule as a row with rule_type
                relevance_row = _flatten(json_object["relevance_rule"])
                relevance_row["rule_type"] = "Relevance"
                rows.append(relevance_row)
                
                # Add each priority_rule as a separate row with rule_type
                for priority_rule in json_object["priority_rules"]:
                    priority_row = _flatten(priority_rule)
                    priority_row["rule_type"] = "Priority"
                    rows.append(priority_row)
            else:
                # Standard single object flattening
                rows = [_flatten(json_object)]

        elif isinstance(json_object, list):
            if not json_object:
                raise ValueError("JSON object is empty")

            if not all(isinstance(item, dict) for item in json_object):
                raise ValueError("JSON object list must contain only dictionaries")

            rows = [_flatten(item) for item in json_object]

        else:
            raise ValueError("Not a valid JSON object")

        df = pd.DataFrame(rows)
        
        # Reorder columns to put rule_type and priority first if they exist
        if "rule_type" in df.columns:
            cols = ["rule_type"]
            if "priority" in df.columns:
                cols.append("priority")
            cols.extend([c for c in df.columns if c not in cols])
            df = df[cols]
        
        return df

    except Exception:
        logger.exception("Failed JSON → CSV normalization")
        raise




def json_rules_to_csv_pandas(json_data):
    rows = []

    # -------- Relevance --------
    for rule in json_data.get("relevance", {}).get("rules", []):
        include_logic = rule["include_logic"]
        logic_type = "any_of" if "any_of" in include_logic else "all_of"

        for block in include_logic.get(logic_type, []):
            rows.append({
                "section": "relevance",
                "priority_level": "",
                "rule_id": rule["rule_id"],
                "rule_text": rule["rule_text"],
                "processing_type": rule["processing_type"],
                "logic_type": logic_type,
                "categories": "|".join(block.get("categories", [])),
                "field": block.get("field", ""),
                "values": "|".join(block.get("values", [])),
                "exclude_logic": json.dumps(rule["exclude_logic"]) if rule["exclude_logic"] else ""
            })

    # -------- Priorities --------
    for priority, priority_block in json_data.get("priorities", {}).items():
        for rule in priority_block.get("rules", []):
            include_logic = rule["include_logic"]
            logic_type = "any_of" if "any_of" in include_logic else "all_of"

            for block in include_logic.get(logic_type, []):
                rows.append({
                    "section": "priorities",
                    "priority_level": priority,
                    "rule_id": rule["rule_id"],
                    "rule_text": rule["rule_text"],
                    "processing_type": rule["processing_type"],
                    "logic_type": logic_type,
                    "categories": "|".join(block.get("categories", [])),
                    "field": block.get("field", ""),
                    "values": "|".join(block.get("values", [])),
                    "exclude_logic": json.dumps(rule["exclude_logic"]) if rule["exclude_logic"] else ""
                })

    # -------- Create DataFrame --------
    df = pd.DataFrame(rows, columns=[
        "section",
        "priority_level",
        "rule_id",
        "rule_text",
        "processing_type",
        "logic_type",
        "categories",
        "field",
        "values",
        "exclude_logic",
    ])
    return df
