from typing import Any, Dict, List, Optional

from pydantic import ValidationError

from ..config import LITELLM_MODEL_URGENCY_DETECT
from ..utils import setup_logger
from .llm_prompts import UrgencyDetectionEntailment
from .utils import _ask_llm_async

logger = setup_logger()


async def detect_urgency(
    urgency_rules: List[str], message: str, metadata: Optional[dict] = None
) -> Dict[str, Any]:
    """
    Detects the urgency of a message based on a set of urgency rules.
    """


    ud_entailment = UrgencyDetectionEntailment(urgency_rules=urgency_rules)
    prompt = ud_entailment.get_prompt()

    json_str = await _ask_llm_async(
        question=message,
        prompt=prompt,
        litellm_model=LITELLM_MODEL_URGENCY_DETECT,
        metadata=metadata,
    )

    try:
        parsed_json = ud_entailment.parse_json(json_str)
    except (ValidationError, ValueError) as e:
        logger.warning(f"JSON Decode failed. json_str: {json_str}. Exception: {e}")
        parsed_json = ud_entailment.default_json

    return parsed_json
