from typing import List, Optional, Literal, Dict

# ---------------------------------------------------------------------------------------------------------------
# Input File Validation Config
# ---------------------------------------------------------------------------------------------------------------

class ValidationConfig:
    MANDATORY_CSV_HEADERS: Dict[str, List[str]] = {
        "client_keywords": ["keyword"],
        "rules": ["priority", "rule"],
        "custom_synonyms": ["id", "term", "root", "synonym"],
    }

    OPTIONAL_CSV_HEADERS: Dict[str, List[str]] = {
        "client_keywords": ["label", "category", "priority"],
        "rules": [],
        "custom_synonyms": [],
    }

    ALLOWED_PRIORITIES: List[str] = [
        "Relevance",
        "Very High",
        "High",
        "Internal",
        "Medium",
        "Low",
        "Not Relevant",
    ]