import csv
import logging
from typing import Tuple, List
from prioritization.config.constants import ValidationConfig

logger = logging.getLogger(__name__)


def validate_csv_content(file_content: str, file_type: str) -> None:
    """
    Validate CSV file content for the given file_type.

    Args:
        file_content: Full CSV file contents as a string (may be None).
        file_type: Key present in ValidationConfig.MANDATORY_CSV_HEADERS.

    Behavior:
        - Raises ValueError if validation fails.
        - Returns None on success.
    """
    if file_content is None:
        # "rules" file is mandatory; other file types are optional.
        if file_type == "rules":
            raise ValueError(f"Required file '{file_type}' is missing.")
        return  # Optional files can be None

    is_valid, errors = _validate_csv(file_content, file_type)
    if not is_valid:
        error_msg = f"Validation failed for '{file_type}':\n  - " + "\n  - ".join(errors)
        raise ValueError(error_msg)


def _validate_csv(file_content: str, file_type: str) -> Tuple[bool, List[str]]:
    """
    Internal CSV validator.

    Returns:
        (is_valid, errors):
            is_valid: True if validation passes, False otherwise.
            errors: list of human-readable error messages.
    """
    errors: List[str] = []

    # 1. File Type Validation
    if file_type not in ValidationConfig.MANDATORY_CSV_HEADERS:
        return False, [
            f"Unknown file_type '{file_type}'. Allowed: "
            f"{list(ValidationConfig.MANDATORY_CSV_HEADERS.keys())}"
        ]

    mandatory_headers = ValidationConfig.MANDATORY_CSV_HEADERS[file_type]
    optional_headers = ValidationConfig.OPTIONAL_CSV_HEADERS.get(file_type, [])

    # 2. Empty content check
    if not file_content or not file_content.strip():
        return False, [f"File content is empty in '{file_type}'"]

    # Clean BOM or weird characters at start
    file_content = file_content.lstrip("\ufeff")

    try:
        lines = file_content.splitlines()
        reader = csv.DictReader(lines)

        # 3. Header presence
        if reader.fieldnames is None:
            return False, [f"File content is empty or missing headers in '{file_type}'"]

        # Header validation
        found_headers = set(reader.fieldnames)
        mandatory_set = set(mandatory_headers)
        optional_set = set(optional_headers)
        allowed_set = mandatory_set | optional_set

        missing_mandatory = mandatory_set - found_headers
        disallowed_extra = found_headers - allowed_set

        if missing_mandatory or disallowed_extra:
            header_errors = []
            if missing_mandatory:
                header_errors.append(f"Missing mandatory headers: {sorted(missing_mandatory)}")
            if disallowed_extra:
                header_errors.append(f"Unexpected headers: {sorted(disallowed_extra)}")
            return False, [
                f"Invalid headers in '{file_type}'. " + "; ".join(header_errors)
            ]

        # For non-rules files, only headers are validated
        if file_type != "rules":
            return True, []

        # 4. 'rules' file: validate rows
        priority_counts = {p: 0 for p in ValidationConfig.ALLOWED_PRIORITIES}
        # Sort allowed priorities by length descending to catch "Very High" before "High"
        sorted_allowed = sorted(
            ValidationConfig.ALLOWED_PRIORITIES,
            key=len,
            reverse=True,
        )

        for line_number, row in enumerate(reader, start=2):
            # NOTE: keys are lowercase to match headers: "priority", "rule"
            priority_val = (row.get("priority") or "").strip()
            rule_val = (row.get("rule") or "").strip()

            # Flexible Priority checks (allow suffixes like "High Priority (comments)")
            matched_priority = None
            lowered_priority_val = priority_val.lower()
            for p in sorted_allowed:
                if lowered_priority_val.startswith(p.lower()):
                    matched_priority = p
                    break

            # Priority checks
            if not priority_val:
                errors.append(
                    f"Row {line_number}: Missing value for 'Priority'"
                )
            elif not matched_priority:
                errors.append(
                    f"Row {line_number}: Invalid Priority '{priority_val}'. "
                    f"Must start with one of: {ValidationConfig.ALLOWED_PRIORITIES}"
                )
            else:
                priority_counts[matched_priority] += 1

            # Rule checks
            if not rule_val:
                errors.append(
                    f"Row {line_number}: Missing or empty value for 'Rule'"
                )

        # 5. AFTER processing all rows: enforce 0-or-1 rule per priority
        for prio, count in priority_counts.items():
            if count > 1:
                errors.append(
                    f"Priority '{prio}' appears {count} times; "
                    "each allowed priority may appear at most once."
                )

        # 6. New business rules:
        #    - "Relevance" is mandatory (must appear exactly once due to rule above).
        #    - At least one other priority (not "Relevance") must be present.
        relevance_count = priority_counts.get("Relevance", 0)
        if relevance_count == 0:
            errors.append(
                "Priority 'Relevance' is required and must appear exactly once."
            )

        # Count all non-'Relevance' priorities
        other_priorities_count = sum(
            count for prio, count in priority_counts.items() if prio != "Relevance"
        )
        if other_priorities_count == 0:
            errors.append(
                "At least one row with a non-'Relevance' priority is required. "
                "Valid non-'Relevance' priorities are: "
                f"{[p for p in ValidationConfig.ALLOWED_PRIORITIES if p != 'Relevance']}"
            )

    except csv.Error as e:
        errors.append(f"CSV parsing error: {e}")
    except Exception:
        logger.exception(
            "Unexpected error while validating CSV for file_type '%s'",
            file_type,
        )
        errors.append("Unexpected error during validation.")

    return len(errors) == 0, errors