from datetime import datetime
from typing import Dict, List, Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Table,
    Column,
    ForeignKey,
    JSON,
    DateTime,
    Integer,
    String,
    delete,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..models import Base
from .schemas import TagCreate

content_tags_table = Table(
    "content_tags",
    Base.metadata,
    Column("content_id", Integer, ForeignKey("content.content_id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tag.tag_id"), primary_key=True),
)


class TagDB(Base):
    __tablename__ = "tag"

    tag_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    tag_name: Mapped[str] = mapped_column(String(length=50), nullable=False)
    created_datetime_utc: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_datetime_utc: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    # Relationship back to content
    contents = relationship(
        "ContentDB", secondary=content_tags_table, back_populates="content_tags"
    )

    def __repr__(self):
        return f"<Tag(tag_name='{self.tag_name}')>"


async def save_tag_to_db(
    tag: TagCreate,
    asession: AsyncSession,
) -> TagDB:
    """
    Saves a tag in the database
    """

    tag_db = TagDB(
        tag_name=tag.tag_name,
        created_datetime_utc=datetime.utcnow(),
        updated_datetime_utc=datetime.utcnow(),
    )

    asession.add(tag_db)

    await asession.commit()
    await asession.refresh(tag_db)

    return tag_db


async def update_tag_in_db(
    tag_id: int,
    tag: TagCreate,
    asession: AsyncSession,
) -> TagDB:
    """
    Updates a tag in the database
    """

    tag_db = TagDB(
        tag_id=tag_id,
        tag_name=tag.tag_name,
        created_datetime_utc=datetime.utcnow(),
        updated_datetime_utc=datetime.utcnow(),
    )

    tag_db = await asession.merge(tag_db)
    await asession.commit()
    await asession.refresh(tag_db)

    return tag_db


async def delete_tag_from_db(
    tag_id: int,
    asession: AsyncSession,
) -> None:
    """
    Deletes a tag from the database
    """
    stmt = delete(TagDB).where(TagDB.tag_id == tag_id)
    await asession.execute(stmt)
    await asession.commit()


async def get_tag_from_db(
    tag_id: int,
    asession: AsyncSession,
) -> Optional[TagDB]:
    """
    Retrieves a tag from the database
    """
    stmt = select(TagDB).where(TagDB.tag_id == tag_id)
    tag_row = (await asession.execute(stmt)).first()
    if tag_row:
        return tag_row[0]
    else:
        return None


async def get_list_of_tags_from_db(
    asession: AsyncSession, offset: int = 0, limit: Optional[int] = None
) -> List[TagDB]:
    """
    Retrieves all Tags from the database
    """
    stmt = select(TagDB).order_by(TagDB.tag_id)
    if offset > 0:
        stmt = stmt.offset(offset)
    if limit is not None:
        stmt = stmt.limit(limit)
    tag_rows = (await asession.execute(stmt)).all()

    return [c[0] for c in tag_rows] if tag_rows else []
