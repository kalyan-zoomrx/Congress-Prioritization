import litellm
from dotenv import load_dotenv
from configuration.config import LitellmConfig
from prioritization.utils.utils import get_prompt
from prioritization.utils.logger import get_logger
from typing import List, Optional
import os

load_dotenv()
litellm.drop_params = True

logger = get_logger(__name__)


def call_llm_with_tracing(
    messages: List[dict],
    model_name: Optional[str] = None,
    stream: bool = False,
    **kwargs
):
    if not model_name:
        model_name = LitellmConfig.DEFAULT_MODEL
        logger.info(f"Default model used: {model_name}")

    try:
        response = litellm.completion(
            base_url=os.environ["LITELLM_ENDPOINT"],
            api_key=os.environ["LITELLM_API_KEY"],
            model=model_name,
            messages=messages,
            stream=stream,
            temperature=0.0,
            **kwargs
        )

        return response if stream else response.choices[0].message

    except KeyError as e:
        logger.critical("Missing required environment variable", exc_info=e)
        raise RuntimeError("LLM configuration error") from e
    except Exception as e:
        logger.exception("Error calling LLM")
        raise


def call_llm_with_user_prompt(
    prompt_name: str,
    format_params: Optional[dict] = None,
    model_name: Optional[str] = None,
    stream: bool = False,
    **kwargs
):
    prompt = get_prompt(prompt_name)
    if format_params:
        try:
            prompt = prompt.format(**format_params)
        except KeyError as e:
            raise ValueError(f"Missing format param: {e}") from e

    messages = [{"role": "user", "content": prompt}]

    return call_llm_with_tracing(
        messages=messages,
        model_name=model_name,
        stream=stream,
        **kwargs
    )


def call_llm_with_system_prompt(
    system_prompt_name: str,
    user_message: str,
    format_params: Optional[dict] = None,
    model_name: Optional[str] = None,
    stream: bool = False,
    **kwargs
):
    system_message = get_prompt(system_prompt_name)
    if format_params:
        try:
            system_message = system_message.format(**format_params)
        except KeyError as e:
            raise ValueError(f"Missing format param: {e}") from e

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]

    return call_llm_with_tracing(
        messages=messages,
        model_name=model_name,
        stream=stream,
        **kwargs
    )