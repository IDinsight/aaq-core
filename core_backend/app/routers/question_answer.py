from datetime import datetime
from typing import Dict

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from litellm import embedding
from qdrant_client import QdrantClient, models
from sqlalchemy.ext.asyncio import AsyncSession

from ..configs.app_config import (
    EMBEDDING_MODEL,
    QDRANT_COLLECTION_NAME,
    QDRANT_N_TOP_SIMILAR,
)
from ..db.db_models import Feedback, UserQuery
from ..db.engine import get_async_session
from ..db.vector_db import get_qdrant_client
from ..schemas import (
    FeedbackBase,
    UserQueryBase,
    UserQueryResponse,
    UserQuerySearchResult,
)

router = APIRouter()


@router.post("/embeddings-search")
async def embeddings_search(
    user_query: UserQueryBase,
    asession: AsyncSession = Depends(get_async_session),
    qdrant_client: QdrantClient = Depends(get_qdrant_client),
) -> UserQueryResponse:
    """
    Embeddings search finds the most similar embeddings to the user query
    from the vector db.
    """

    feedback_secret_key = generate_secret_key()
    user_query_db = UserQuery(
        feedback_secret_key=feedback_secret_key,
        query_datetime_utc=datetime.utcnow(),
        **user_query.model_dump(),
    )
    asession.add(user_query_db)
    await asession.commit()
    await asession.refresh(user_query_db)

    return UserQueryResponse(
        query_id=user_query_db.query_id,
        responses=get_similar_content(
            user_query, qdrant_client, int(QDRANT_N_TOP_SIMILAR)
        ),
        feedback_secret_key=feedback_secret_key,
    )


@router.post("/feedback")
async def feedback(
    feedback: FeedbackBase, asession: AsyncSession = Depends(get_async_session)
) -> JSONResponse:
    """
    Feedback endpoint used to capture user feedback on the results returned
    """

    is_matched = await check_secret_key_match(
        feedback.feedback_secret_key, feedback.query_id
    )

    if is_matched is False:
        return JSONResponse(
            status_code=400,
            content={
                "message": f"Secret key does not match query id : {feedback.query_id}"
            },
        )
    else:
        feedback_db = Feedback(
            feedback_datetime_utc=datetime.utcnow(),
            query_id=feedback.query_id,
            feedback_text=feedback.feedback_text,
        )
        asession.add(feedback_db)
        await asession.commit()
        await asession.refresh(feedback_db)
        return JSONResponse(
            status_code=200, content={"message": f"Added : {feedback_db.feedback_id}"}
        )


async def check_secret_key_match(secret_key: str, query_id: int) -> bool:
    """
    Check if the secret key matches the one generated for query id
    """
    return True


def generate_secret_key() -> str:
    """
    Generate a secret key for the user query
    """
    return "abc1234"


def get_similar_content(
    question: UserQueryBase,
    qdrant_client: QdrantClient,
    n_similar: int,
) -> Dict[int, UserQuerySearchResult]:
    """
    Get the most similar points in the vector db
    """

    question_embedding = (
        embedding(EMBEDDING_MODEL, question.query_text).data[0].embedding
    )

    search_result = qdrant_client.search(
        collection_name=QDRANT_COLLECTION_NAME,
        query_vector=question_embedding,
        limit=n_similar,
        with_payload=models.PayloadSelectorInclude(include=["content_text"]),
    )

    results_dict = {}
    for i, r in enumerate(search_result):
        if r.payload is None:
            raise ValueError("Payload is empty. No content text found.")
        else:
            results_dict[i] = UserQuerySearchResult(
                response_text=r.payload.get("content_text", ""),
                score=r.score,
            )

    return results_dict
