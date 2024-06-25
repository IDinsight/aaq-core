from typing import Optional

from litellm import acompletion

from ..config import LITELLM_API_KEY, LITELLM_ENDPOINT, LITELLM_MODEL_DEFAULT
from ..utils import setup_logger

logger = setup_logger("LLM_call")


async def _ask_llm_async(
    question: str,
    prompt: str,
    litellm_model: Optional[str] = LITELLM_MODEL_DEFAULT,
    litellm_endpoint: Optional[str] = LITELLM_ENDPOINT,
    metadata: Optional[dict] = None,
    json: bool = False,
) -> str:
    """
    This is a generic function to ask the LLM model a question.
    """
    if metadata is not None:
        metadata["generation_name"] = litellm_model

    extra_kwargs = {}
    if json:
        extra_kwargs["response_format"] = {"type": "json_object"}

    messages = [
        {
            "content": prompt,
            "role": "system",
        },
        {
            "content": question,
            "role": "user",
        },
    ]
    logger.info(f"LLM input: 'model': {litellm_model}, 'endpoint': {litellm_endpoint}")

    llm_response_raw = await acompletion(
        model=litellm_model,
        messages=messages,
        temperature=0,
        max_tokens=1024,
        api_base=litellm_endpoint,
        api_key=LITELLM_API_KEY,
        metadata=metadata,
        **extra_kwargs,
    )
    logger.info(f"LLM output: {llm_response_raw.choices[0].message.content}")
    return llm_response_raw.choices[0].message.content


def remove_json_markdown(text: str) -> str:
    """Remove json markdown from text."""

    json_str = text.removeprefix("```json").removesuffix("```").strip()
    json_str = json_str.replace("\{", "{").replace("\}", "}")

    return json_str
