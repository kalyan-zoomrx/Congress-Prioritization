# Rule Analysis Workflow

This document provides a detailed overview of the **Rule Analysis** step within the Congress Prioritization system. This step is responsible for ingesting raw prioritization rules, client keywords, and synonyms, and transforming them into a structured JSON format using Large Language Models (LLMs) with iterative refinement.

---

## Overview

The Rule Analysis component is implemented as a set of [LangGraph](https://www.langchain.com/langgraph) nodes within the `RuleAnalysisNodes` class. Its primary goal is to take unstructured or semi-structured CSV data and produce a validated, machine-readable JSON schema that governs the prioritization logic.

## Architecture & Logic

The workflow is managed by the `RuleAnalysisNodes` class located in [rule_analysis.py](file:///c:/Users/HemaKalyanMurapaka/Desktop/Congress%20Prioritization/prioritization/components/rule_analysis.py). It follows a standard pipeline:

1.  **Data Loading**: Ingesting raw CSV files.
2.  **Rule Parsing**: Orchestrating LLM calls to translate rules into JSON.
3.  **Validation**: Programmatically verifying the LLM's output.
4.  **Iterative Refinement**: Re-prompting the LLM if validation fails.
5.  **Persistence**: Saving the final validated JSON.

### 1. Data Loading (`load_data`)

The system expects three primary input files in the specified project directory:

- `rules.csv`: The core prioritization rules.
- `client_keywords.csv`: Keywords specific to the client.
- `custom_synonyms.csv` (Optional): Custom synonym mappings.

These are read and stored in the `PrioritizationState` under `rules_raw`, `keywords_raw`, and `synonyms_raw`.

### 2. Rule Parsing (`parse_rules`)

This node coordinates the interaction with the LLM via the `call_llm_with_user_prompt` utility.

- **Prompting**: It uses the `rule_parsing_prompt` template.
- **Context**: The prompt is populated with the raw input data and any previous `validation_errors`.
- **Response Handling**: The system attempts to parse the LLM's response as JSON. It includes a fallback using `ast.literal_eval` for robustness against minor formatting issues (like single quotes).

### 3. Validation (`validate_rules`)

After parsing, the output is subjected to programmatic checks:

- Ensures the output is a valid dictionary.
- Verifies the presence of mandatory top-level keys: `relevance` and `priorities`.
- Collects any errors into the `validation_errors` list in the state.

### 4. Refinement Mechanism

If `validation_errors` is not empty, the workflow loops back to `parse_rules`. The subsequent prompt includes a specific "Refinement required" section listing the errors to be corrected. The `iteration_count` tracks these attempts.

### 5. Saving Output (`save_output`)

Once validation passes (or iterations are exhausted), the final JSON is saved to the `outputs` folder defined in `LitellmConfig`.

- **Filename Format**: `parsed_rules_{timestamp}_{model_name}.json`
- **Example**: `parsed_rules_2025-12-23_14-30-00_gemini-1.5-pro.json`

---

## Data State (`PrioritizationState`)

The workflow maintains state using a `TypedDict` defined in [state.py](file:///c:/Users/HemaKalyanMurapaka/Desktop/Congress%20Prioritization/prioritization/utils/state.py):

| Field               | Type             | Description                                           |
| :------------------ | :--------------- | :---------------------------------------------------- |
| `directory`         | `str`            | Working directory for inputs/outputs.                 |
| `model`             | `str`            | LLM model identifier (e.g., `gemini/gemini-1.5-pro`). |
| `rules_raw`         | `Optional[str]`  | Raw content of `rules.csv`.                           |
| `keywords_raw`      | `Optional[str]`  | Raw content of `client_keywords.csv`.                 |
| `parsed_rules`      | `Optional[Dict]` | The JSON output from the LLM.                         |
| `validation_errors` | `List[str]`      | List of errors found during validation.               |
| `iteration_count`   | `int`            | Number of parsing attempts made.                      |

---

## Output Structure

The resulting JSON follows a structured schema that includes:

- `relevance`: Logic for determining if a record matches the project scope.
- `priorities`: A hierarchical list of rules assigned to specific priority levels.

For more details on the JSON schema, refer to `prioritization/Rule Parsing Schema.json`.
