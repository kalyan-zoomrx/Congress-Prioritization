from typing import TypedDict, List, Dict, Any, Optional

class PrioritizationState(TypedDict):
    directory: str
    model: str
    user_instructions: Optional[str]
    rules_raw: Optional[str]
    keywords_raw: Optional[str]
    synonyms_raw: Optional[str]
    parsed_rules: Optional[Dict[str, Any]]
    validation_errors: List[str]
    iteration_count: int
    output_file: Optional[str]

class RuleAnalysisState(TypedDict):
    directory: str
    model: str
    rules_raw: Optional[str]
    keywords_raw: Optional[str]
    analysis_report: Optional[Dict[str, Any]]
    review_decision: Optional[str]
    user_feedback: Optional[str]
    review_history: List[Dict[str, Any]]
    iteration_count: int
    report_path: Optional[str]
