from pathlib import Path
from typing import List, Tuple

import pytest
import yaml

from core_backend.app.llm_call.llm_prompts import IdentifiedLanguage
from core_backend.app.llm_call.parse_input import _identify_language
from core_backend.app.question_answer.schemas import UserQueryRefined, UserQueryResponse

pytestmark = pytest.mark.rails


LANGUAGE_FILE = "data/language_identification.yaml"


@pytest.fixture(scope="module")
def available_languages() -> list[str]:
    """Returns a list of available languages"""

    return [lang.value for lang in IdentifiedLanguage]


def read_test_data(file: str) -> List[Tuple[str, str]]:
    """Reads test data from file and returns a list of strings"""

    file_path = Path(__file__).parent / file

    with open(file_path, "r") as f:
        content = yaml.safe_load(f)
        return [(key, value) for key, values in content.items() for value in values]


@pytest.mark.parametrize("language, content", read_test_data(LANGUAGE_FILE))
async def test_language_identification(
    available_languages: list[str], language: str, content: str
) -> None:
    """Test language identification"""
    question = UserQueryRefined(query_text=content, query_text_original=content)
    response = UserQueryResponse(
        query_id=1,
        content_response=None,
        llm_response="Dummy response",
        feedback_secret_key="feedback-string",
    )
    if language not in available_languages:
        language = "UNKNOWN"
    _, response = await _identify_language(question, response)
    assert response.debug_info["original_language"] == language
