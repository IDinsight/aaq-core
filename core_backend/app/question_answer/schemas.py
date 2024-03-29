from enum import Enum
from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict

from ..llm_call.llm_prompts import IdentifiedLanguage


class UserQueryBase(BaseModel):
    """
    Pydantic model for query APIs
    """

    query_text: str
    query_metadata: dict = {}

    model_config = ConfigDict(from_attributes=True)


class UserQueryRefined(UserQueryBase):
    """
    Pydantic model for refined query
    """

    query_text_original: str
    original_language: IdentifiedLanguage | None = None


class UserQuerySearchResult(BaseModel):
    """
    Pydantic model for each individual search result
    """

    retrieved_title: str
    retrieved_text: str
    score: float

    model_config = ConfigDict(from_attributes=True)


class ResultState(str, Enum):
    """
    Enum for Response state
    """

    FINAL = "final"
    IN_PROGRESS = "in_progress"
    ERROR = "error"


class ErrorType(str, Enum):
    """
    Enum for Error Type
    """

    QUERY_UNSAFE = "query_unsafe"
    UNKNOWN_LANGUAGE = "unknown_language"
    UNABLE_TO_TRANSLATE = "unable_to_translate"
    UNABLE_TO_PARAPHRASE = "unable_to_paraphrase"
    ALIGNMENT_TOO_LOW = "alignment_too_low"


class UserQueryResponse(BaseModel):
    """
    Pydantic model for response to Query
    """

    query_id: int
    content_response: Dict[int, UserQuerySearchResult] | None
    llm_response: Optional[str] = None
    feedback_secret_key: str
    debug_info: dict = {}
    state: ResultState = ResultState.IN_PROGRESS

    model_config = ConfigDict(from_attributes=True)


class UserQueryResponseError(BaseModel):
    """
    Pydantic model when there is an error
    """

    query_id: int
    error_message: Optional[str] = None
    error_type: ErrorType
    debug_info: dict = {}

    model_config = ConfigDict(from_attributes=True)


class FeedbackBase(BaseModel):
    """
    Pydantic model for feedback
    """

    query_id: int
    feedback_text: str
    feedback_secret_key: str

    model_config = ConfigDict(from_attributes=True)
