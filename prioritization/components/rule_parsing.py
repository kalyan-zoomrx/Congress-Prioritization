import os
import json
import ast
from datetime import datetime
from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from prioritization.utils.logger import get_logger
from prioritization.config.config import LitellmConfig
from prioritization.utils.state import PrioritizationState
from prioritization.utils.litellm import call_llm_with_user_prompt
from prioritization.schema.schema import RuleParsingOutputConfig

logger = get_logger("RuleParsingNodes")

class RuleParsingNodes:
    def __init__(self):
        pass

    # ------------------------------------------------------------------------------------------
    # Loading Data
    # ------------------------------------------------------------------------------------------

    def load_data(self, state: PrioritizationState) -> PrioritizationState:
        """Loads data idempotentally: uses state if present, else loads from disk."""
        logger.info("Rule Parsing: Loading Data")
        
        state["current_main_step"] = "Rule Parsing"
        state["current_sub_step"] = "Data Loading"
        state["step_status"] = "in_progress"

        directory = state.get("directory")
        if not directory:
            state.update({"step_status": "failed", "step_error": "Missing 'directory' key"})
            return state
        
        def read_file(name: str, required: bool = False):
            path = os.path.join(directory, name)
            if not os.path.exists(path):
                if required: raise FileNotFoundError(f"Missing: {path}")
                return None
            with open(path, "r", encoding="utf-8") as f:
                return f.read().strip()

        try:
            # Idempotent loading: bypass disk if already in state (chaining support)
            if not state.get("rules_raw"):
                state["rules_raw"] = read_file("rules.csv", required=True)
                logger.info("Loaded rules.csv from disk")
            else:
                logger.info("Using pre-populated rules_raw from state")

            if not state.get("keywords_raw"):
                state["keywords_raw"] = read_file("client_keywords.csv", required=True)
                logger.info("Loaded client_keywords.csv from disk")
            else:
                logger.info("Using pre-populated keywords_raw from state")

            if not state.get("synonyms_raw"):
                state["synonyms_raw"] = read_file("custom_synonyms.csv")
                logger.info("Loaded custom_synonyms.csv from disk" if state["synonyms_raw"] else "No custom_synonyms.csv found")
            else:
                logger.info("Using pre-populated synonyms_raw from state")

        except Exception as e:
            logger.error(f"Error loading data: {e}")
            state.update({"step_status": "failed", "step_error": str(e)})
        
        return state


    # ------------------------------------------------------------------------------------------
    # Parsing Logic
    # ------------------------------------------------------------------------------------------

    def parse_rules(self, state: PrioritizationState) -> PrioritizationState:
        """LangGraph Node: Parses rules using LLM, handles refinement, and updates state."""
        if state.get("step_status") == "failed":
            return state

        logger.info("Rule Parsing: Invoking AI")
        state["current_sub_step"] = "AI Parsing"
        current_iter = state.get("iteration_count", 0)

        # [1] Preparing instructions
        base_instructions = state.get("user_instructions", "")
        refinement_instructions = ""
        if state.get("validation_errors"):
            refinement_instructions = f"\nRefinement required. Please correct errors: {', '.join(state['validation_errors'])}"

        full_instructions = f"{base_instructions}{refinement_instructions}".strip()

        # [2] Calling the LLM
        try:
            response = call_llm_with_user_prompt(
                prompt_name="rule_parsing_prompt",
                format_params={
                    "rules": state.get("transformed_rules") or state["rules_raw"],
                    "client_keywords": state["keywords_raw"],
                    "custom_synonyms": state.get("synonyms_raw") or "None provided",
                    "user_instructions": full_instructions
                },
                model_name=state["model"],
                json_output=True,
                json_schema = RuleParsingOutputConfig
            )

            content = response.content.replace("```json", "").replace("```", "").strip()
            try:
                state["parsed_rules"] = json.loads(content)
            except Exception:
                state["parsed_rules"] = ast.literal_eval(content)
            
            logger.info("Rule parsing completed successfully")
        except Exception as e:
            logger.error(f"Error during Parsing Rules node: {e}")
            state.update({"step_status": "failed", "step_error": str(e)})

        state["iteration_count"] = current_iter + 1
        return state

    

    # ------------------------------------------------------------------------------------------
    # Validation Logic
    # ------------------------------------------------------------------------------------------

    def validate_rules(self, state: PrioritizationState) -> PrioritizationState:
        """Programmatic & Syntactic validation of the LLM output."""
        if state.get("step_status") == "failed":
            return state

        logger.info("Rule Parsing: Validating Output")
        state["current_sub_step"] = "Validation"
        
        errors = []
        parsed = state.get("parsed_rules")

        if not parsed or not isinstance(parsed, dict):
            errors.append("Output is not a valid JSON dictionary.")
        else:
            if "relevance" not in parsed:
                errors.append("Missing mandatory 'relevance' key.")
            if "priorities" not in parsed:
                errors.append("Missing mandatory 'priorities' key.")
            
        if errors:
            logger.warning(f"Validation failed: {errors}")
        else:
            logger.info("Validation successful")
            
        state["validation_errors"] = errors
        return state


    # ------------------------------------------------------------------------------------------
    # Saving Parsed Rules
    # ------------------------------------------------------------------------------------------
        
    def save_output(self, state: PrioritizationState) -> PrioritizationState:
        """Final node to persist the validated JSON to disk."""
        if state.get("step_status") == "failed":
            return state

        logger.info("Rule Parsing: Saving Parsed Rules")
        state["current_sub_step"] = "Saving Output"
        
        try:
            directory = state["directory"]
            os.makedirs(os.path.join(directory, LitellmConfig.OUTPUT_FOLDER), exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            model_tag = state.get("model", "unknown").split("/")[-1]
            output_filename = f"parsed_rules_{timestamp}_{model_tag}.json"
            output_path = os.path.join(directory, LitellmConfig.OUTPUT_FOLDER, output_filename)
            
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(state["parsed_rules"], f, indent=2)
                
            state.update({
                "output_file": output_path,
                "step_status": "success"
            })
        except Exception as e:
            logger.error(f"Error saving output: {e}")
            state.update({"step_status": "failed", "step_error": str(e)})

        return state