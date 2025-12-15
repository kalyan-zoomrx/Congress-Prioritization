import os
from functools import lru_cache
from prioritization.utils.logger import get_logger

logger = get_logger(__name__)


@lru_cache(maxsize=128)
def get_prompt(prompt_name: str):
    try:
        with open(f"prioritization/prompts/{prompt_name}.txt", "r") as f:
            prompt = f.read()
            logger.info(f"Prompt {prompt_name} read successfully")
            return prompt

    except FileNotFoundError:
        logger.error(f"Prompt {prompt_name} not found")
        raise
    except Exception as e:
        logger.error(f"Error reading prompt {prompt_name}: {str(e)}")
        raise