from collections import namedtuple
from typing import Union

import numpy as np
import pytest
from fastapi.testclient import TestClient

from core_backend.app import create_app
from core_backend.app.configs.app_config import QDRANT_VECTOR_SIZE

Fixture = Union

EmbeddingData = namedtuple("EmbeddingData", "data")
EmbeddingValues = namedtuple("EmbeddingValues", "embedding")


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
    monkeysession.setattr("app.routers.manage_content.embedding", fake_embedding)
    monkeysession.setattr("app.routers.question_answer.embedding", fake_embedding)


def fake_embedding(*arg: str, **kwargs: str) -> EmbeddingData:
    """
    Replicates `litellm.embedding` function but just generates a random
    list of floats
    """

    embedding_list = np.random.rand(int(QDRANT_VECTOR_SIZE)).astype(np.float32).tolist()
    embedding = EmbeddingValues(embedding_list)
    data_obj = EmbeddingData([embedding])

    return data_obj
