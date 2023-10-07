import json
import uuid

import pytest
from app.configs.app_config import (
    EMBEDDING_MODEL,
    QDRANT_COLLECTION_NAME,
    QDRANT_N_TOP_SIMILAR,
)
from app.db.vector_db import get_qdrant_client
from fastapi.testclient import TestClient
from litellm import embedding
from qdrant_client.models import PointStruct


class TestEmbeddingsSearch:
    @pytest.fixture
    def upload_data(self, client: TestClient) -> None:
        with open("tests/data/content.json", "r") as f:
            json_data = json.load(f)

        points = []
        for content in json_data:
            point_id = str(uuid.uuid4())
            content_embedding = (
                embedding(EMBEDDING_MODEL, content["content_text"]).data[0].embedding
            )
            payload = content.get("content_metadata", {})
            points.append(
                PointStruct(id=point_id, vector=content_embedding, payload=payload)
            )

        qdrant_client = get_qdrant_client()
        qdrant_client.upsert(collection_name=QDRANT_COLLECTION_NAME, points=points)

    def test_question_answer(
        self, client: TestClient, upload_data: pytest.FixtureRequest
    ) -> None:
        response = client.post(
            "/embeddings-search",
            json={"query_text": "Tell me about a good sport to play"},
        )
        assert response.status_code == 200
        json_response = response.json()

        assert len(json_response.keys()) == int(QDRANT_N_TOP_SIMILAR)

    @pytest.fixture
    def upload_questions(self, client: TestClient) -> None:
        response = client.post(
            "/embeddings-search",
            json={
                "query_text": "Tell me about a good sport to play",
            },
        )
        return response.json()

    def test_feedback(
        self, client: TestClient, upload_questions: pytest.FixtureRequest
    ) -> None:
        query_id = upload_questions["query_id"]
        feedback_secret_key = upload_questions["feedback_secret_key"]

        response = client.post(
            "/feedback",
            json={
                "feedback_text": "This is feedback",
                "query_id": query_id,
                "feedback_secret_key": feedback_secret_key,
            },
        )
        assert response.status_code == 200
