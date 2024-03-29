from datetime import datetime
from typing import Dict, List, Optional

from litellm import aembedding, embedding
from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    JSON,
    DateTime,
    Integer,
    String,
    delete,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from ..config import LITELLM_EMBEDDING_MODEL
from ..contents.config import PGVECTOR_VECTOR_SIZE
from ..models import Base, JSONDict
from .schemas import (
    ContentCreate,
    ContentUpdate,
)


class ContentDB(Base):
    """
    SQL Alchemy data model for content
    """

    __tablename__ = "content"

    content_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    content_embedding: Mapped[Vector] = mapped_column(
        Vector(int(PGVECTOR_VECTOR_SIZE)), nullable=False
    )
    content_title: Mapped[str] = mapped_column(String(length=150), nullable=False)
    content_text: Mapped[str] = mapped_column(String(length=2000), nullable=False)
    content_language: Mapped[str] = mapped_column(String, nullable=False)

    content_metadata: Mapped[JSONDict] = mapped_column(JSON, nullable=False)

    created_datetime_utc: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_datetime_utc: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    def __repr__(self) -> str:
        """Pretty Print"""
        return f"<Content #{self.content_id}:  {self.content_text}>"


async def save_content_to_db(
    content: ContentCreate,
    asession: AsyncSession,
) -> ContentDB:
    """
    Vectorizes and saves a content in the database
    """

    content_embedding = await _get_content_embeddings(content)

    content_db = ContentDB(
        content_embedding=content_embedding,
        content_title=content.content_title,
        content_text=content.content_text,
        content_language=content.content_language,
        content_metadata=content.content_metadata,
        created_datetime_utc=datetime.utcnow(),
        updated_datetime_utc=datetime.utcnow(),
    )

    asession.add(content_db)

    await asession.commit()
    await asession.refresh(content_db)

    return content_db


async def update_content_in_db(
    content_id: int,
    content: ContentCreate,
    asession: AsyncSession,
) -> ContentDB:
    """
    Updates a content and vector in the database
    """

    content_embedding = await _get_content_embeddings(content)
    content_db = ContentDB(
        content_id=content_id,
        content_embedding=content_embedding,
        content_title=content.content_title,
        content_text=content.content_text,
        content_language=content.content_language,
        content_metadata=content.content_metadata,
        updated_datetime_utc=datetime.utcnow(),
    )

    content_db = await asession.merge(content_db)
    await asession.commit()
    return content_db


async def delete_content_from_db(
    content_id: int,
    asession: AsyncSession,
) -> None:
    """
    Deletes a content from the database
    """
    stmt = delete(ContentDB).where(ContentDB.content_id == content_id)
    await asession.execute(stmt)
    await asession.commit()


async def get_content_from_db(
    content_id: int,
    asession: AsyncSession,
) -> Optional[ContentDB]:
    """
    Retrieves a content from the database
    """
    stmt = select(ContentDB).where(ContentDB.content_id == content_id)
    content_row = (await asession.execute(stmt)).first()
    if content_row:
        return content_row[0]
    else:
        return None


async def get_list_of_content_from_db(
    asession: AsyncSession, offset: int = 0, limit: Optional[int] = None
) -> List[ContentDB]:
    """
    Retrieves all content from the database
    """
    stmt = select(ContentDB).order_by(ContentDB.content_id)
    if offset > 0:
        stmt = stmt.offset(offset)
    if limit is not None:
        stmt = stmt.limit(limit)
    content_rows = (await asession.execute(stmt)).all()

    return [c[0] for c in content_rows] if content_rows else []


async def _get_content_embeddings(
    content: ContentCreate | ContentUpdate,
) -> List[float]:
    """
    Vectorizes the content
    """
    text_to_embed = content.content_title + "\n" + content.content_text
    content_embedding = embedding(LITELLM_EMBEDDING_MODEL, text_to_embed).data[0][
        "embedding"
    ]
    return content_embedding


async def get_similar_content(
    question: str,
    n_similar: int,
    asession: AsyncSession,
) -> Dict[int, tuple[str, str, float]]:
    """
    Get the most similar points in the vector table
    """
    response = embedding(LITELLM_EMBEDDING_MODEL, question)
    question_embedding = response.data[0]["embedding"]

    return await get_search_results(
        question_embedding,
        n_similar,
        asession,
    )


async def get_similar_content_async(
    question: str, n_similar: int, asession: AsyncSession
) -> Dict[int, tuple[str, str, float]]:
    """
    Get the most similar points in the vector table
    """
    response = await aembedding(LITELLM_EMBEDDING_MODEL, question)
    question_embedding = response.data[0]["embedding"]

    return await get_search_results(
        question_embedding,
        n_similar,
        asession,
    )


async def get_search_results(
    question_embedding: List[float], n_similar: int, asession: AsyncSession
) -> Dict[int, tuple[str, str, float]]:
    """Get similar content to given embedding and return search results"""
    query = (
        select(
            ContentDB,
            ContentDB.content_embedding.cosine_distance(question_embedding).label(
                "distance"
            ),
        )
        .order_by(ContentDB.content_embedding.cosine_distance(question_embedding))
        .limit(n_similar)
    )
    search_result = (await asession.execute(query)).all()

    results_dict = {}
    for i, r in enumerate(search_result):
        results_dict[i] = (r[0].content_title, r[0].content_text, r[1])

    return results_dict
