import os
import time
import litellm
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List, Optional, Type, Union

from prioritization.config.config import LitellmConfig
from prioritization.utils.utils import get_prompt
from prioritization.utils.logger import get_logger

load_dotenv()
litellm.drop_params = True

logger = get_logger("LiteLLM Utils")

PROVIDER_MODELS = {
    "openai": ["gpt-4.1"],
    "anthropic": ["claude-haiku-4-5"],
    "gemini": ["gemini/gemini-2.5-pro"]
}

def _get_provider_from_model(model_name: str) -> str:
    for provider, models in PROVIDER_MODELS.items():
        if model_name in models:
            return provider
    return "unknown"

def _build_kwargs(provider: str, json_output: bool, json_schema: Optional[Union[Type[BaseModel], dict]] = None) -> dict:
    """
    Build provider-specific kwargs for structured / JSON output.
    Supports:
      - OpenAI: response_format (json_schema/json_object)
      - Anthropic: betas + output_format (json_schema/json)
      - Gemini: response_mime_type + response_json_schema
    """

    if not json_output:
        logger.info("Proceeding without JSON/structured output")
        return {}

    # Normalize Schema: Pydantic Model/Dict -> Dict
    schema_dict: Optional[dict] = None
    if json_schema is not None:
        if isinstance(json_schema, type) and issubclass(json_schema, BaseModel):
            schema_dict = json_schema.model_json_schema()
        elif isinstance(json_schema, dict):
            schema_dict = json_schema
        else:
            raise TypeError("json_schema must be either a Pydantic BaseModel subclass or a dict")

    if provider == "openai":
        if schema_dict is not None:
            logger.info("Proceeding with OpenAI JSON output schema")
            return {
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {
                        "strict": True,
                        "schema": schema_dict
                    }
                }
            }
        else:
            logger.info("Proceeding with OpenAI JSON output without schema")
            return {
                "response_format": {
                    "type": "json_object"
                }
            }

    if provider == "anthropic":
        if schema_dict is not None:
            logger.info("Proceeding with Anthropic JSON output schema")
            return {
                "betas": ["structured-outputs-2025-11-13"],
                "output_format": {
                    "type": "json_schema",
                    "schema": schema_dict,
                },
            }
        else:
            logger.info("Proceeding with Anthropic JSON output without schema")
            return {
                "betas": ["structured-outputs-2025-11-13"],
                "output_format": {
                    "type": "json"
                },
            }

    if provider == "gemini":
        if schema_dict is not None:
            logger.info("Proceeding with Gemini JSON output schema")
            return {
                "response_mime_type": "application/json",
                "response_json_schema": schema_dict
            }
        else:
            logger.info("Proceeding with Gemini JSON output without schema")
            return {
                "response_mime_type": "application/json"
            }
    
    else:
        logger.warning(f"Provider {provider} not supported for JSON schema; proceeding without schema kwargs")
        return {}

def call_llm_with_tracing(
    messages: List[dict],
    model_name: Optional[str] = None,
    stream: bool = False,
    json_output: bool = False,
    json_schema: Optional[Union[Type[BaseModel], dict]] = None,
    **kwargs
):

    if not model_name:
        model_name = LitellmConfig.DEFAULT_MODEL
        logger.info(f"Default model used: {model_name}")
    else:
        logger.info(f"Model used: {model_name}")
    
    provider = _get_provider_from_model(model_name)
    logger.info(f"Identified Provider: {provider}")

    provider_json_kwargs = _build_kwargs(
        provider=provider,
        json_output=json_output,
        json_schema=json_schema,
    )

    final_kwargs = {**provider_json_kwargs, **kwargs}
    logger.info("Json Format Args: %s", final_kwargs)
    
    try:
        start_time = time.time()
        response = litellm.completion(
            base_url=os.environ["LITELLM_ENDPOINT"],
            api_key=os.environ["LITELLM_API_KEY"],
            model=model_name,
            messages=messages,
            stream=stream,
            temperature=0.0,
            **final_kwargs
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
    json_output: bool = False,
    json_schema: Optional[Union[Type[BaseModel], dict]] = None,
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
        json_schema=json_schema,
        **kwargs
    )


def call_llm_with_system_prompt(
    system_prompt_name: str,
    user_message: str,
    format_params: Optional[dict] = None,
    model_name: Optional[str] = None,
    stream: bool = False,
    json_output: bool = False,
    json_schema: Optional[Union[Type[BaseModel], dict]] = None,
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
        json_schema=json_schema,
        **kwargs
    )