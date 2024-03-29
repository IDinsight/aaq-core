"""
These are functions to check the LLM response
"""

from functools import wraps
from typing import Any, Callable, TypedDict

from pydantic import ValidationError

from ..config import (
    ALIGN_SCORE_API,
    ALIGN_SCORE_METHOD,
    ALIGN_SCORE_THRESHOLD,
    LITELLM_ENDPOINT_ALIGNSCORE,
    LITELLM_MODEL_ALIGNSCORE,
)
from ..question_answer.schemas import (
    UserQueryRefined,
    UserQueryResponse,
    UserQueryResponseError,
)
from ..utils import get_http_client, setup_logger
from .llm_prompts import AlignmentScore
from .utils import _ask_llm_async

logger = setup_logger("OUTPUT RAILS")


class AlignScoreData(TypedDict):
    """
    Payload for the AlignScore API
    """

    evidence: str
    claim: str


def check_align_score__after(func: Callable) -> Callable:
    """
    Check the alignment score
    """

    @wraps(func)
    async def wrapper(
        question: UserQueryRefined,
        response: UserQueryResponse | UserQueryResponseError,
        *args: Any,
        **kwargs: Any,
    ) -> UserQueryResponse | UserQueryResponseError:
        """
        Check the alignment score
        """

        llm_response = await func(question, response, *args, **kwargs)

        if isinstance(llm_response, UserQueryResponseError):
            return llm_response

        if llm_response.llm_response is None:
            logger.warning(
                (
                    "No LLM response found in the LLM response but "
                    "`check_align_score` was called"
                )
            )
            return llm_response
        else:
            return await _check_align_score(llm_response)

    return wrapper


async def _check_align_score(
    llm_response: UserQueryResponse,
) -> UserQueryResponse:
    """
    Check the alignment score
    """

    evidence = _build_evidence(llm_response)
    claim = llm_response.llm_response
    assert claim is not None, "LLM response is None"
    align_score_date = AlignScoreData(evidence=evidence, claim=claim)

    if ALIGN_SCORE_METHOD is None:
        logger.warning(
            "No alignment score method specified but `check_align_score` was called"
        )
        return llm_response

    elif ALIGN_SCORE_METHOD == "AlignScore":
        if ALIGN_SCORE_API is not None:
            align_score = await _get_alignScore_score(ALIGN_SCORE_API, align_score_date)
        else:
            raise ValueError("Method is AlignScore but ALIGN_SCORE_API is not set.")
    elif ALIGN_SCORE_METHOD == "LLM":
        align_score = await _get_llm_align_score(align_score_date)
    else:
        raise NotImplementedError(f"Unknown method {ALIGN_SCORE_METHOD}")

    factual_consistency = {
        "method": ALIGN_SCORE_METHOD,
        "score": align_score.score,
        "reason": align_score.reason,
        "claim": claim,
    }

    if align_score.score < float(ALIGN_SCORE_THRESHOLD):
        llm_response.llm_response = None

    llm_response.debug_info["factual_consistency"] = factual_consistency.copy()

    return llm_response


async def _get_alignScore_score(
    api_url: str, align_score_date: AlignScoreData
) -> AlignmentScore:
    """
    Get the alignment score from the AlignScore API
    """
    async with get_http_client().post(api_url, json=align_score_date) as resp:
        if resp.status != 200:
            logger.error(f"AlignScore API request failed with status {resp.status}")
            raise RuntimeError(
                f"AlignScore API request failed with status {resp.status}"
            )

        result = await resp.json()
    logger.info(f"AlignScore result: {result}")
    alignment_score = AlignmentScore(score=result["alignscore"], reason="N/A")

    return alignment_score


async def _get_llm_align_score(align_score_data: AlignScoreData) -> AlignmentScore:
    """
    Get the alignment score from the LLM
    """
    prompt = AlignmentScore.prompt.format(context=align_score_data["evidence"])
    result = await _ask_llm_async(
        prompt,
        align_score_data["claim"],
        litellm_model=LITELLM_MODEL_ALIGNSCORE,
        litellm_endpoint=LITELLM_ENDPOINT_ALIGNSCORE,
    )

    try:
        alignment_score = AlignmentScore.model_validate_json(result)
    except ValidationError as e:
        logger.error(f"LLM alignment score respone is not valid json: {e}")

    logger.info(f"LLM Alignment result: {alignment_score.model_dump_json()}")

    return alignment_score


def _build_evidence(llm_response: UserQueryResponse) -> str:
    """
    Build the evidence used by the LLM response
    """
    evidence = ""
    if llm_response.content_response is not None:
        for _, result in llm_response.content_response.items():
            evidence += result.retrieved_text + "\n"
    return evidence
