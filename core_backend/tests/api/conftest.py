import json
import uuid
from collections import namedtuple
from typing import Union

import httpx
import numpy as np
import pytest
from fastapi.testclient import TestClient
from qdrant_client.models import PointStruct

from core_backend.app import create_app
from core_backend.app.auth import create_access_token
from core_backend.app.configs.app_config import (
    EMBEDDING_MODEL,
    QDRANT_COLLECTION_NAME,
    QDRANT_VECTOR_SIZE,
)
from core_backend.app.db.vector_db import get_qdrant_client
from core_backend.app.llm_call import parse_input
from core_backend.app.routers.manage_content import _create_payload_for_qdrant_upsert

Fixture = Union

# Define namedtuples for the embedding endpoint
EmbeddingData = namedtuple("EmbeddingData", "data")
EmbeddingValues = namedtuple("EmbeddingValues", "embedding")

# Define namedtuples for the completion endpoint
CompletionData = namedtuple("CompletionData", "choices")
CompletionChoice = namedtuple("CompletionChoice", "message")
CompletionMessage = namedtuple("CompletionMessage", "content")


@pytest.fixture(scope="session")
def faq_contents(client: TestClient) -> None:
    with open("tests/api/data/content.json", "r") as f:
        json_data = json.load(f)

    points = []
    for content in json_data:
        point_id = str(uuid.uuid4())
        text_to_embed = content["content_title"] + "\n" + content["content_text"]
        content_embedding = fake_embedding(EMBEDDING_MODEL, text_to_embed).data[0][
            "embedding"
        ]
        metadata = content.get("content_metadata", {})
        payload = _create_payload_for_qdrant_upsert(
            content["content_title"], content["content_text"], metadata
        )
        points.append(
            PointStruct(
                id=point_id, vector=content_embedding, payload=payload.model_dump()
            )
        )

    qdrant_client = get_qdrant_client()
    qdrant_client.upsert(collection_name=QDRANT_COLLECTION_NAME, points=points)


@pytest.fixture(scope="session")
def client(patch_llm_call: pytest.FixtureRequest) -> TestClient:
    app = create_app()
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def monkeysession(request: pytest.FixtureRequest) -> pytest.FixtureRequest:
    from _pytest.monkeypatch import MonkeyPatch

    mpatch = MonkeyPatch()
    yield mpatch
    mpatch.undo()


@pytest.fixture(scope="session", autouse=True)
def patch_llm_call(monkeysession: pytest.FixtureRequest) -> None:
    """
    Monkeypatch call to LLM embeddings service
    """
    monkeysession.setattr(
        "core_backend.app.routers.manage_content.embedding", fake_embedding
    )
    monkeysession.setattr("core_backend.app.db.vector_db.embedding", fake_embedding)
    monkeysession.setattr(parse_input, "_classify_safety", lambda a, b: (a, b))
    monkeysession.setattr(parse_input, "_identify_language", lambda a, b: (a, b))
    monkeysession.setattr(parse_input, "_paraphrase_question", lambda a, b: (a, b))
    monkeysession.setattr(parse_input, "_translate_question", lambda a, b: (a, b))

    monkeysession.setattr(
        "core_backend.app.routers.question_answer.get_llm_rag_answer",
        lambda *args, **kwargs: "monkeypatched_llm_response",
    )


def fake_embedding(*arg: str, **kwargs: str) -> EmbeddingData:
    """
    Replicates `litellm.embedding` function but just generates a random
    list of floats
    """

    embedding_list = np.random.rand(int(QDRANT_VECTOR_SIZE)).astype(np.float32).tolist()
    data_obj = EmbeddingData([{"embedding": embedding_list}])

    return data_obj


@pytest.fixture(scope="session")
def fullaccess_token() -> str:
    """
    Returns a token with full access
    """
    return create_access_token("fullaccess")


@pytest.fixture(scope="session")
def readonly_token() -> str:
    """
    Returns a token with readonly access
    """
    return create_access_token("readonly")


@pytest.fixture(scope="session", autouse=True)
def patch_httpx_call(monkeysession: pytest.FixtureRequest) -> None:
    """
    Monkeypatch call to httpx service
    """

    class MockClient:
        async def __aenter__(self) -> "MockClient":
            return self

        async def __aexit__(self, exc_type: str, exc: str, tb: str) -> None:
            pass

        async def post(self, *args: str, **kwargs: str) -> httpx.Response:
            return httpx.Response(200, json={"status": "success"})

    monkeysession.setattr(httpx, "AsyncClient", MockClient)
