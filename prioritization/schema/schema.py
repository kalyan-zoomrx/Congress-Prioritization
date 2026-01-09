from dataclasses import field
from typing import List, Optional, Literal
from pydantic import BaseModel, ConfigDict, Field
from enum import Enum



# ---------------------------------------------------------------------------------------------------------------
# Rule Analysis Schema Config
# ---------------------------------------------------------------------------------------------------------------

class PriorityLevel(str, Enum):
    RELEVANCE = "Relevance"
    VERY_HIGH = "Very High"
    HIGH = "High"
    INTERNAL = "Internal"
    MEDIUM = "Medium"
    LOW = "Low"
    NOT_RELEVANT = "Not Relevant"


class IssueSeverity(str, Enum):
    CRITICAL = "Critical"
    WARNING = "Warning"


class Issue(BaseModel):
    issue: str = Field(
        ...,
        description=(
            "Short description of the problem. "
            "May include 'CRITICAL' or 'WARNING' wording in the text if desired."
        ),
    )
    priority_levels: List[PriorityLevel] = Field(
        ...,
        description=(
            "Priority levels involved in this issue. "
            "Must not contain 'Relevance' at runtime."
        ),
    )
    severity: IssueSeverity = Field(
        ...,
        description="Critical for true logical collisions; Warning for broader ambiguities.",
    )
    impact: str = Field(
        ...,
        description="One concise sentence explaining why the issue matters."
    )


class OptimizationEntry(BaseModel):
    priority_level: PriorityLevel = Field(
        ...,
        description=(
            "Priority level to which the following original and suggested texts apply. "
            "Include 'Relevance' only if that level appears in RULES."
        ),
    )
    original_text: str = Field(
        ...,
        description=(
            "All original rule texts for this level combined into a single numbered list "
            "string (e.g., '1. ...\\n2. ...'), copied exactly from RULES."
        ),
    )
    suggested_text: str = Field(
        ...,
        description=(
            "Refined/optimized numbered list of rules for this level, or empty string if "
            "no optimization is proposed. Must be empty for Relevance."
        ),
    )
    rationale: str = Field(
        ...,
        description=(
            "Brief explanation (1-3 sentences) of the changes or clarifications for this "
            "level, focused on mutual exclusivity within conceptual categories. Must be "
            "empty for Relevance or when suggested_text is empty."
        ),
    )


class RuleAnalysisOutputConfig(BaseModel):
    issues: List[Issue] = Field(
        ...,
        description=(
            "Logical conflicts, overlaps, or ambiguities identified in the prioritization "
            "rules (excluding Relevance)."
        ),
    )
    optimizations: List[OptimizationEntry] = Field(
        ...,
        description=(
            "One entry per priority level present in RULES (plus Relevance if present), "
            "ordered logically as: Relevance → Very High → High → Internal → Medium → "
            "Low → Not Relevant."
        ),
    )


# ---------------------------------------------------------------------------------------------------------------
# Parsing Output Schema Config
# ---------------------------------------------------------------------------------------------------------------

ProcessingType = Literal["keyword_filtering", "context_filtering", "hybrid_filtering", "none"]
EntityType = Literal["concepts", "keywords", "contextual-keywords", "columns"]

class Condition(BaseModel):
    entities: EntityType
    values: List[str]

class LogicBlock(BaseModel):
    all_of: Optional[List[Condition]] = None
    any_of: Optional[List[Condition]] = None

class Rule(BaseModel):
    rule_id: str
    rule_text: str
    processing_type: ProcessingType
    reasoning: str
    include_logic: LogicBlock
    exclude_logic: Optional[LogicBlock] = None

class RelevanceConfig(BaseModel):
    rules: List[Rule]

class PriorityLevel(BaseModel):
    rules: List[Rule]

class PrioritiesConfig(BaseModel):
    very_high: PriorityLevel = Field(alias="Very High")
    high: PriorityLevel = Field(alias="High")
    internal: PriorityLevel = Field(alias="Internal")
    medium: PriorityLevel = Field(alias="Medium")
    low: PriorityLevel = Field(alias="Low")
    not_relevant: PriorityLevel = Field(alias="Not Relevant")
    model_config = ConfigDict(validate_by_name=True)

class RuleParsingOutputConfig(BaseModel):
    relevance: RelevanceConfig
    priorities: PrioritiesConfig