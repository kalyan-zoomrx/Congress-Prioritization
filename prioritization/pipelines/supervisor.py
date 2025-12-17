import os
import sys
import json
from prioritization.components.rule_analysis import RuleParserAgent
from prioritization.utils.logger import get_logger
from datetime import datetime

from prioritization.evaluation.evaluate_rule_analysis import evaluate_parsed_rules
from prioritization.utils.utils import normalize_json_to_dataframe

logger = get_logger("Supervisor")

def initiate_supervisor(directory: str, model: str = None):
    # --------------------------------------------------------------------------------------------------
    # Rule Analysis
    # --------------------------------------------------------------------------------------------------
    
    rule_parser_agent = RuleParserAgent()

    if os.path.exists(directory + "rules.csv"):
        if os.path.exists(directory + "client_keywords.csv"):
            if not os.path.exists(directory + "custom_synonyms.csv"):
                logger.info("Processing Rules & Client Keywords, Custom Synonyms not found")
                response = rule_parser_agent.parse_rules(
                    rules_file=directory + "rules.csv",
                    client_keywords_file=directory + "client_keywords.csv",
                    model=model
                )
            
                os.makedirs(directory + "output", exist_ok=True)
                OUTPUT_FILE = directory + "output/parsed_rules_" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + "_" + model.split("/")[-1] + ".xlsx"
                rule_parsed_df = normalize_json_to_dataframe(response)
                rule_parsed_df.to_excel(OUTPUT_FILE, index=False)
            

            elif os.path.exists(directory + "custom_synonyms.csv"):
                logger.info("Processing Rules & Client Keywords, Custom Synonyms")
                response = rule_parser_agent.parse_rules(
                    rules_file=directory + "rules.csv",
                    client_keywords_file=directory + "client_keywords.csv",
                    custom_synonyms_file=directory + "custom_synonyms.csv",
                    model=model
                )
                
                os.makedirs(directory + "output", exist_ok=True)
                OUTPUT_FILE = directory + "output/parsed_rules_" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + "_" + model.split("/")[-1] + ".xlsx"
                rule_parsed_df = normalize_json_to_dataframe(response)
                rule_parsed_df.to_excel(OUTPUT_FILE, index=False)
        
    else:
        logger.error("Rules or Client Keywords file not found")

# --------------------------------------------------------------------------------------------------
# Rule Analysis Evaluation
# --------------------------------------------------------------------------------------------------
'''
metrics = evaluate_parsed_rules(
    rules_file=TEST_DIRECTORY + "rules.csv",
    client_keywords_file=TEST_DIRECTORY + "client_keywords.csv",
    parsed_rules_file=OUTPUT_FILE,
    custom_synonyms_file=TEST_DIRECTORY + "custom_synonyms.csv" if os.path.exists(TEST_DIRECTORY + "custom_synonyms.csv") else None,
    output_report_path=TEST_DIRECTORY + "output/evaluation_report_" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".json"
)


'''