import csv
import logging
from typing import Tuple, List
from prioritization.config.config import ValidationConfig

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
        error_msg = f"Validation failed for '{file_type}': ".join(errors)
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
            f"Unknown file_type '{file_type}'. Allowed: {list(ValidationConfig.MANDATORY_CSV_HEADERS.keys())}"
        ]

    expected_headers = ValidationConfig.MANDATORY_CSV_HEADERS[file_type]

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

        # Header validation (order-insensitive; exact set)
        found_headers = set(reader.fieldnames)
        expected_header_set = set(expected_headers)

        missing = expected_header_set - found_headers
        extra = found_headers - expected_header_set

        if missing or extra:
            header_errors = []
            if missing:
                header_errors.append(f"Missing headers: {sorted(missing)}")
            if extra:
                header_errors.append(f"Unexpected headers: {sorted(extra)}")
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
            priority_val = (row.get("Priority") or "").strip()
            rule_val = (row.get("Rule") or "").strip()

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
                    f"Row {line_number}: Invalid Priority '{priority_val}'. Must start with one of: {ValidationConfig.ALLOWED_PRIORITIES}"
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
                    f"Priority '{prio}' appears {count} times; each allowed priority may appear at most once."
                )

        # 6. Ensure at least one priority is present
        total_priorities = sum(priority_counts.values())
        if total_priorities == 0:
            errors.append(
                f"At least one row with a valid 'Priority' is required. Valid priorities must start with one of: {ValidationConfig.ALLOWED_PRIORITIES}"
            )

    except csv.Error as e:
        errors.append(f"CSV parsing error: {e}")
    except Exception as e:
        # Log unexpected errors for debugging/monitoring
        logger.exception(
            "Unexpected error while validating CSV for file_type '%s'",
            file_type,
        )
        errors.append("Unexpected error during validation.")

    return len(errors) == 0, errors