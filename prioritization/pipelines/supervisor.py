import os
import json
from prioritization.components.rule_analysis import RuleParserAgent
from prioritization.utils.logger import get_logger
from datetime import datetime

logger = get_logger("Supervisor")

TEST_DIRECTORY = "data/test01_ASCO_2025_RevMed/"

logger.info("Initiated Supervisor")

rule_parser_agent = RuleParserAgent()

if os.path.exists(TEST_DIRECTORY + "rules.csv") and os.path.exists(TEST_DIRECTORY + "client_keywords.csv"):
    if not os.path.exists(TEST_DIRECTORY + "custom_synonyms.csv"):
        response = rule_parser_agent.parse_rules(
            rules_file=TEST_DIRECTORY + "rules.csv",
            client_keywords_file=TEST_DIRECTORY + "client_keywords.csv",
        )
        
        os.makedirs(TEST_DIRECTORY + "output", exist_ok=True)
        with open(TEST_DIRECTORY + "output/parsed_rules_" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".json", "w", encoding="utf-8") as f:
            json.dump(response, f, indent=2)

    elif os.path.exists(TEST_DIRECTORY + "custom_synonyms.csv"):
        response = rule_parser_agent.modify_rules(
            rules_file=TEST_DIRECTORY + "rules.csv",
            client_keywords_file=TEST_DIRECTORY + "client_keywords.csv",
            custom_synonyms_file=TEST_DIRECTORY + "custom_synonyms.csv",
        )
        
        os.makedirs(TEST_DIRECTORY + "output", exist_ok=True)
        with open(TEST_DIRECTORY + "output/parsed_rules_" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".json", "w", encoding="utf-8") as f:
            json.dump(response, f, indent=2)
    
else:
    logger.error("Rules or Client Keywords file not found")
        
