import os
import json
from datetime import datetime
from prioritization.utils.logger import get_logger
from prioritization.utils.state import PrioritizationState
from prioritization.components.rule_analysis import RuleParserAgent

logger = get_logger("PrioritizationNodes")

class PrioritizationNodes:
    def __init__(self):
        self.agent = RuleParserAgent()

    def load_data(self, state: PrioritizationState) -> PrioritizationState:
        """Reads input CSV files from the directory and stores them in the state."""

        logger.info("Loading Input Data")
        directory = state["directory"]
        
        # Load primary rules and keywords
        with open(os.path.join(directory, "rules.csv"), "r", encoding="utf-8") as f:
            state["rules_raw"] = f.read()
        
        with open(os.path.join(directory, "client_keywords.csv"), "r", encoding="utf-8") as f:
            state["keywords_raw"] = f.read()
            
        # Load optional synonyms
        synonyms_path = os.path.join(directory, "custom_synonyms.csv")
        if os.path.exists(synonyms_path):
            with open(synonyms_path, "r", encoding="utf-8") as f:
                state["synonyms_raw"] = f.read()
        else:
            state["synonyms_raw"] = None
                
        return state

    def parse_rules(self, state: PrioritizationState) -> PrioritizationState:
        """Sends the data to the LLM. Includes feedback if it's a retry."""
        current_iter = state.get("iteration_count", 0)
        logger.info(f"Node: Parsing Rules (Attempt {current_iter + 1})")
        
        # Use the agent initialized in __init__
        response = self.agent.parse_rules(
            rules_file=os.path.join(state["directory"], "rules.csv"),
            client_keywords_file=os.path.join(state["directory"], "client_keywords.csv"),
            custom_synonyms_file=os.path.join(state["directory"], "custom_synonyms.csv") if state["synonyms_raw"] else None,
            model=state["model"]
        )
        
        state["parsed_rules"] = response
        state["iteration_count"] = current_iter + 1
        return state

    def validate_rules(self, state: PrioritizationState) -> PrioritizationState:
        """Programmatic validation of the LLM output."""
        logger.info("Node: Validating Output")
        errors = []
        parsed = state.get("parsed_rules")
        
        # Basic Schema Validation based on rule_parsing_prompt.txt
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

        
    def save_output(self, state: PrioritizationState) -> PrioritizationState:
        """Final node to persist the validated JSON to the disk."""
        logger.info("Node: Saving Output")
        directory = state["directory"]
        os.makedirs(os.path.join(directory, "output"), exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_filename = f"parsed_rules_{timestamp}_{state['model'].replace('/', '-')}.json"
        output_path = os.path.join(directory, "output", output_filename)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(state["parsed_rules"], f, indent=4)
            
        state["output_file"] = output_path
        logger.info(f"Workflow complete. Saved to: {output_path}")
        return state
