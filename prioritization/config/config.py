from dataclasses import dataclass, field
from typing import Dict, List

@dataclass
class LitellmConfig:
    MAX_RETRIES: int = 3
    DEFAULT_MODEL: str = "gpt-4.1"
    OUTPUT_FOLDER: str = "output"

class ValidationConfig:
    MANDATORY_CSV_HEADERS: Dict[str, List[str]] = {
        "client_keywords": ["keyword", "label", "category"],
        "rules": ["Priority", "Rule"],
        "custom_synonyms": ["id", "term", "root", "synonym"]
    }
    ALLOWED_PRIORITIES: List[str] = [
        "Very High",
        "High",
        "Internal",
        "Medium",
        "Low",
        "Not Relevant"
    ]