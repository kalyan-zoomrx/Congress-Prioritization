import litellm
from dotenv import load_dotenv
from configuration.config import LitellmConfig
from prioritization.utils.utils import get_prompt
from prioritization.utils.logger import get_logger
from typing import List, Optional
import os
import time

load_dotenv()
litellm.drop_params = True

logger = get_logger("LiteLLM Utils")

PROVIDER_MODELS = {
    "openai": ["gpt-4.1"],
    "anthropic": ["claude-haiku-4-5"],
    "gemini": ["gemini/gemini-2.5-pro"]
}

PROVIDER_JSON_KWARGS = {
    "openai": lambda: {"response_format": {"type": "json_object"}},

    "anthropic": lambda: {"betas": ["structured-outputs-2025-11-13"], "output_format": {"type": "json"}},

    "gemini": lambda: {"response_mime_type": "application/json"}
}

def _get_provider_from_model(model_name: str) -> str:
    for provider, models in PROVIDER_MODELS.items():
        if model_name in models:
            return provider
    return "unknown"

def call_llm_with_tracing(
    messages: List[dict],
    model_name: Optional[str] = None,
    stream: bool = False,
    json_output: Optional[bool] = False,
    **kwargs
):

    if not model_name:
        model_name = LitellmConfig.DEFAULT_MODEL
        logger.info(f"Default model used: {model_name}")
    else:
        logger.info(f"Model used: {model_name}")
    
    provider = _get_provider_from_model(model_name)
    logger.info(f"Identified Provider: {provider}")

    if json_output:
        if provider in PROVIDER_JSON_KWARGS:
            kwargs.update(PROVIDER_JSON_KWARGS[provider]())
            logger.info(f"JSON Schema enabled for {provider}: {PROVIDER_JSON_KWARGS[provider]()}")
        else:
            logger.warning(f"Provider is not supported for JSON Schema: {provider}")
    else:
        logger.info(f"JSON Schema not enabled")
    
    try:
        start_time = time.time()
        response = litellm.completion(
            base_url=os.environ["LITELLM_ENDPOINT"],
            api_key=os.environ["LITELLM_API_KEY"],
            model=model_name,
            messages=messages,
            stream=stream,
            temperature=0.0,
            **kwargs
        )
        end_time = time.time()
        logger.info(f"LLM call took {end_time - start_time:.2f} seconds")
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
    json_output: Optional[bool] = False,
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
        json_output=json_output,
        **kwargs
    )


def call_llm_with_system_prompt(
    system_prompt_name: str,
    user_message: str,
    format_params: Optional[dict] = None,
    model_name: Optional[str] = None,
    stream: bool = False,
    json_output: Optional[bool] = False,
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
        json_output=json_output,
        **kwargs
    )