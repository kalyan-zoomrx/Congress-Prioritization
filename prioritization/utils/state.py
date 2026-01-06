from typing import TypedDict, List, Dict, Any, Optional

class PrioritizationState(TypedDict):
    # Main Artifacts and Configuration
    directory: str
    model: str
    rules_raw: Optional[str]
    keywords_raw: Optional[str]
    synonyms_raw: Optional[str]

    # Global Pipeline Status
    current_step: str
    step_status: str
    step_error: Optional[str]

    # Rule Analysis Specifics
    analysis_report: Optional[Dict[str, Any]]
    review_decision: Optional[str]
    user_feedback: Optional[str]
    review_history: List[Dict[str, Any]]
    analysis_iteration_count: int
    report_path: Optional[str]
    transformed_rules: Optional[str]

    # Rule Parsing Specifics
    user_instructions: Optional[str]
    parsed_rules: Optional[Dict[str, Any]]
    validation_errors: List[str]
    parsing_iteration_count: int
    output_file: Optional[str]