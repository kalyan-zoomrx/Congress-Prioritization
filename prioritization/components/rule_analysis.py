import os
import json
import ast
from typing import Dict, Any, Optional
from datetime import datetime
from prioritization.utils.logger import get_logger
from prioritization.utils.state import PrioritizationState
from prioritization.utils.litellm import call_llm_with_user_prompt

logger = get_logger("RuleAnalysisNodes")

class RuleAnalysisNodes:
    def __init__(self):
        pass

    # ------------------------------------------------------------------------------------------
    # Loading Data
    # ------------------------------------------------------------------------------------------

    def load_data(self, state: PrioritizationState) -> PrioritizationState:
        """Reads input CSV files from the directory and stores them in the state."""

        logger.info("Loading Input Data")
        directory = state["directory"]
        
        try:
            with open(os.path.join(directory, "rules.csv"), "r", encoding="utf-8") as f:
                state["rules_raw"] = f.read()
            
            with open(os.path.join(directory, "client_keywords.csv"), "r", encoding="utf-8") as f:
                state["keywords_raw"] = f.read()
                
            synonyms_path = os.path.join(directory, "custom_synonyms.csv")
            if os.path.exists(synonyms_path):
                with open(synonyms_path, "r", encoding="utf-8") as f:
                    state["synonyms_raw"] = f.read()
                    logger.info("Loaded Inputs: rules.csv, client_keywords.csv, custom_synonyms.csv")
            else:
                state["synonyms_raw"] = None
                logger.info("Loaded Inputs: rules.csv, client_keywords.csv. Proceeding without custom_synonyms.csv")
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise
        
        return state


    # ------------------------------------------------------------------------------------------
    # Parsing Logic
    # ------------------------------------------------------------------------------------------

    def parse_rules(self, state: PrioritizationState) -> PrioritizationState:
        """LangGraph Node: Parses rules using LLM, handles refinement, and updates state."""
        
        logger.info("Initializing Rule Parsing")
        current_iter = state.get("iteration_count", 0)
        logger.info(f"Parsing Rules (Attempt {current_iter + 1})")

        # [1] Preparing instructions (User Instructions + Validation Feedback)
        base_instructions = state.get("user_instructions", "")
        if base_instructions:
            logger.info(f"Base User Instructions: {base_instructions}")

        refinement_instructions = ""
        if state.get("validation_errors"):
            refinement_instructions = f"\nRefinement required. Please correct the following errors from your previous output: {', '.join(state['validation_errors'])}"
            logger.warning(f"Adding Refinement Instructions: {refinement_instructions}")

        full_instructions = f"{base_instructions}{refinement_instructions}".strip()

        # [2] Calling the LLM
        try:
            response = call_llm_with_user_prompt(
                prompt_name="rule_parsing_prompt",
                format_params={
                    "rules": state["rules_raw"],
                    "client_keywords": state["keywords_raw"],
                    "custom_synonyms": state.get("synonyms_raw"),
                    "user_instructions": full_instructions
                },
                model_name=state["model"],
                json_output=True
            )

            # [3] Clean and Parse the LLM Response
            content = response.content.replace("```json", "").replace("```", "").strip()
            try:
                state["parsed_rules"] = json.loads(content)
            except Exception:
                # Fallback for single quotes or other literal formats using safer ast.literal_eval
                state["parsed_rules"] = ast.literal_eval(content)
            
            logger.info("Rule parsing completed successfully")

        except Exception as e:
            logger.error(f"Error during Parsing Rules node: {e}")
            state["parsed_rules"] = None

        state["iteration_count"] = current_iter + 1
        return state

    

    # ------------------------------------------------------------------------------------------
    # Validation Logic
    # ------------------------------------------------------------------------------------------

    def validate_rules(self, state: PrioritizationState) -> PrioritizationState:
        """Programmatic & Syntactic validation of the LLM output of the parsed rules."""

        logger.info("Initializing Rule Validation")
        errors = []
        parsed = state.get("parsed_rules")

        #  Basic Validations
        #   - Check if the output is a valid JSON dictionary
        #   - Check if the output dictionary has the mandatory keys

        if not parsed or not isinstance(parsed, dict):
            errors.append("Output is not a valid JSON dictionary.")
        else:
            if "relevance" not in parsed:
                errors.append("Output dictionary is missing mandatory 'relevance' key.")
            if "priorities" not in parsed:
                errors.append("Output dictionary is missing mandatory 'priorities' key.")
            
        if errors:
            logger.warning(f"Validation failed with errors: {errors}")
        else:
            logger.info("Validation successful")
            
        state["validation_errors"] = errors
        return state


    # ------------------------------------------------------------------------------------------
    # Saving Parsed Rules
    # ------------------------------------------------------------------------------------------
        
    def save_output(self, state: PrioritizationState) -> PrioritizationState:
        """Final node to persist the validated JSON to the disk."""

        logger.info("Saving Parsed Rules")
        directory = state["directory"]
        os.makedirs(os.path.join(directory, "output"), exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        model_name = state.get("model", "unknown").split("/")[-1]
        output_filename = f"parsed_rules_{timestamp}_{model_name}.json"
        output_path = os.path.join(directory, "output", output_filename)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(state["parsed_rules"], f, indent=2)
            
        state["output_file"] = output_path
        logger.info(f"Parsed Rules saved to: {output_path}")
        return state
