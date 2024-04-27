from datetime import datetime
from typing import Optional

from sqlalchemy import (
    DateTime,
    String,
    # delete,
    select,
)
from sqlalchemy.exc import MultipleResultsFound, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from ..models import Base
from ..utils import get_key_hash
from .schemas import UserCreate


class UserDB(Base):
    """
    SQL Alchemy data model for users
    """

    __tablename__ = "user"

    user_id: Mapped[str] = mapped_column(String, primary_key=True, nullable=False)
    username: Mapped[str] = mapped_column(String, nullable=False)

    hashed_retrieval_key: Mapped[str] = mapped_column(String(64), nullable=False)

    created_datetime_utc: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_datetime_utc: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    def __repr__(self) -> str:
        """Pretty Print"""
        return f"<{self.username} mapped to #{self.user_id}>"


async def save_user_to_db(
    user: UserCreate,
    asession: AsyncSession,
) -> UserDB:
    """
    Saves a user in the database
    """

    # Check if user with same username already exists
    stmt = select(UserDB).where(UserDB.username == user.username)
    result = await asession.execute(stmt)
    try:
        result.one()
        raise ValueError(f"User with username {user.username} already exists.")
    except MultipleResultsFound as err:
        raise ValueError(
            f"Multiple users with username {user.username} found in local database."
        ) from err
    except NoResultFound:
        pass

    hashed_retrieval_key = get_key_hash(user.retrieval_key)

    content_db = UserDB(
        user_id=user.user_id,
        username=user.username,
        hashed_retrieval_key=hashed_retrieval_key,
        created_datetime_utc=datetime.utcnow(),
        updated_datetime_utc=datetime.utcnow(),
    )

    asession.add(content_db)
    await asession.commit()
    await asession.refresh(content_db)

    return content_db


async def get_user_by_username(
    username: str,
    asession: AsyncSession,
) -> Optional[UserDB]:
    """
    Retrieves a user by username
    """

    # Check if user with same username already exists
    stmt = select(UserDB).where(UserDB.username == username)
    result = await asession.execute(stmt)
    try:
        user = result.scalar_one()
        return user
    except NoResultFound as err:
        raise ValueError(f"User with username {username} does not exist.") from err


async def get_user_by_token(
    token: str,
    asession: AsyncSession,
) -> Optional[UserDB]:
    """
    Retrieves a user by token
    """

    hashed_token = get_key_hash(token)

    stmt = select(UserDB).where(UserDB.hashed_retrieval_key == hashed_token)
    result = await asession.execute(stmt)
    try:
        user = result.scalar_one()
        return user
    except NoResultFound as err:
        raise ValueError("User with given token does not exist.") from err