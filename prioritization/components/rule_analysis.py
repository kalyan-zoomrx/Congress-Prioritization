import re
from typing import Dict, Any, Tuple, Generator
from prioritization.utils.logger import get_logger
from prioritization.utils.litellm import call_llm_with_user_prompt

logger = get_logger("[1.0] Rule Analysis")

class RuleParserAgent:

    # ----------------------------------------------------------------------------------------
    # Rule Parsing
    # ----------------------------------------------------------------------------------------

    def parse_rules(
        self,
        rules_file: str,
        client_keywords_file: str,
        custom_synonyms_file: str = None,
        model: str = None
    ) -> Dict[str, Any]:
        """
        Parses and analyzes rules using LLM.

        Args:
            state: The current state of the agent.

        Returns:
            A generator that yields streaming chunks and a final result dictionary.
        """
        logger.info("Initiated Rule Parsing")

        try:
            with open(rules_file, "r", encoding="utf-8") as f:
                rules_data = f.read()

            with open(client_keywords_file, "r", encoding="utf-8") as f:
                client_keywords_data = f.read()

            custom_synonyms_data = None
            if custom_synonyms_file:
                with open(custom_synonyms_file, "r", encoding="utf-8") as f:
                    custom_synonyms_data = f.read()

            llm_response = call_llm_with_user_prompt(
                prompt_name="prioritization_rule_analysis_prompt",
                format_params={
                    "rules": rules_data,
                    "client_keywords": client_keywords_data,
                    "custom_synonyms": custom_synonyms_data,
                    "user_instructions": ""
                },
                model_name=model
            )

            # Validating the response for JSON compatibility
            try:
                rule_analysis = eval(llm_response.content)
            except Exception as e:
                logger.error(f"Error parsing LLM response: {e}")
                raise

            logger.info("Rule parsing completed")
            return rule_analysis

        except Exception as e:
            logger.error(f"Error parsing rules: {e}")
            raise