from datetime import datetime
from typing import Dict, List

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from ..schemas import (
    FeedbackBase,
    UserQueryBase,
    UserQueryResponse,
    WhatsAppIncoming,
    WhatsAppResponse,
)

JSONDict = Dict[str, str]


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models"""

    pass


class UserQueryDB(Base):
    """
    SQLAlchemy data model for questions asked by user
    """

    __tablename__ = "user-queries"

    query_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, nullable=False
    )
    feedback_secret_key: Mapped[str] = mapped_column(String, nullable=False)
    query_text: Mapped[str] = mapped_column(String, nullable=False)
    query_metadata: Mapped[JSONDict] = mapped_column(JSON, nullable=False)
    query_datetime_utc: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    feedback: Mapped[List["FeedbackDB"]] = relationship(
        "FeedbackDB", back_populates="query", lazy=True
    )
    response: Mapped[List["UserQueryResponseDB"]] = relationship(
        "UserQueryResponseDB", back_populates="query", lazy=True
    )

    def __repr__(self) -> str:
        """Pretty Print"""
        return f"<Query #{self.query_id}> {self.query_text}>"


async def save_user_query_to_db(
    asession: AsyncSession, feedback_secret_key: str, user_query: UserQueryBase
) -> UserQueryDB:
    """
    Saves a user query to the database.
    """
    user_query_db = UserQueryDB(
        feedback_secret_key=feedback_secret_key,
        query_datetime_utc=datetime.utcnow(),
        **user_query.model_dump(),
    )
    asession.add(user_query_db)
    await asession.commit()
    await asession.refresh(user_query_db)
    return user_query_db


async def check_secret_key_match(
    secret_key: str, query_id: int, asession: AsyncSession
) -> bool:
    """
    Check if the secret key matches the one generated for query id
    """
    stmt = select(UserQueryDB.feedback_secret_key).where(
        UserQueryDB.query_id == query_id
    )
    query_record = (await asession.execute(stmt)).first()

    if (query_record is not None) and (query_record[0] == secret_key):
        return True
    else:
        return False


class UserQueryResponseDB(Base):
    """
    SQLAlchemy data model for responses sent to user
    """

    __tablename__ = "user-query-responses"

    response_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    query_id: Mapped[int] = mapped_column(Integer, ForeignKey("user-queries.query_id"))
    content_response: Mapped[JSONDict] = mapped_column(JSON, nullable=False)
    llm_response: Mapped[str] = mapped_column(String, nullable=True)
    response_datetime_utc: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    query: Mapped[UserQueryDB] = relationship(
        "UserQueryDB", back_populates="response", lazy=True
    )

    def __repr__(self) -> str:
        """Pretty Print"""
        return f"<Responses for query #{self.query_id}"


async def save_query_response_to_db(
    asession: AsyncSession,
    user_query_db: UserQueryDB,
    response: UserQueryResponse,
) -> UserQueryResponseDB:
    """
    Saves the user query response to the database.
    """
    user_query_responses_db = UserQueryResponseDB(
        query_id=user_query_db.query_id,
        content_response=response.model_dump()["content_response"],
        llm_response=response.model_dump()["llm_response"],
        response_datetime_utc=datetime.utcnow(),
    )
    asession.add(user_query_responses_db)
    await asession.commit()
    await asession.refresh(user_query_responses_db)
    return user_query_responses_db


class FeedbackDB(Base):
    """
    SQLAlchemy data model for feedback provided by user
    """

    __tablename__ = "feedback"

    feedback_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, nullable=False
    )
    query_id: Mapped[int] = mapped_column(Integer, ForeignKey("user-queries.query_id"))
    feedback_text: Mapped[str] = mapped_column(String, nullable=False)
    feedback_datetime_utc: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    query: Mapped[UserQueryDB] = relationship(
        "UserQueryDB", back_populates="feedback", lazy=True
    )

    def __repr__(self) -> str:
        """Pretty Print"""
        return (
            f"<Feedback #{self.feedback_id} for query "
            f"#{self.query_id}> {self.feedback_text}"
        )


async def save_feedback_to_db(
    asession: AsyncSession, feedback: FeedbackBase
) -> FeedbackDB:
    """
    Saves feedback to the database.
    """
    feedback_db = FeedbackDB(
        feedback_datetime_utc=datetime.utcnow(),
        query_id=feedback.query_id,
        feedback_text=feedback.feedback_text,
    )
    asession.add(feedback_db)
    await asession.commit()
    await asession.refresh(feedback_db)
    return feedback_db


class WhatsAppMessageDB(Base):
    """
    SQL Alchemy data model for incoming messages from user.
    """

    __tablename__ = "whatsapp_incoming_messages"

    incoming_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    msg_id_from_whatsapp: Mapped[str] = mapped_column(String, nullable=False)
    phone_number: Mapped[str] = mapped_column(String, nullable=False)
    message: Mapped[str] = mapped_column(String, nullable=False)
    phonenumber_id: Mapped[str] = mapped_column(String, nullable=False)
    incoming_datetime_utc: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    response = relationship(
        "WhatsAppResponseDB", back_populates="incoming_message", lazy=True
    )


class WhatsAppResponseDB(Base):
    """
    SQL Alchemy data model for responses sent to user.
    """

    __tablename__ = "whatsapp_responses"

    response_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    incoming_id = mapped_column(
        Integer, ForeignKey("whatsapp_incoming_messages.incoming_id"), nullable=False
    )
    response = mapped_column(String)
    response_datetime_utc: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    response_status: Mapped[int] = mapped_column(Integer, nullable=False)
    incoming_message = relationship(
        "WhatsAppMessageDB", back_populates="response", lazy=True
    )


async def save_wamessage_to_db(
    asession: AsyncSession,
    incoming: WhatsAppIncoming,
) -> WhatsAppMessageDB:
    """
    Saves WhatsApp incoming messages to the database.
    """
    wa_incoming = WhatsAppMessageDB(
        phone_number=incoming.phone_number,
        msg_id_from_whatsapp=incoming.msg_id_from_whatsapp,
        message=incoming.message,
        phonenumber_id=incoming.phone_id,
        incoming_datetime_utc=datetime.utcnow(),
    )
    asession.add(wa_incoming)
    await asession.commit()
    await asession.refresh(wa_incoming)
    return wa_incoming


async def save_waresponse_to_db(
    asession: AsyncSession,
    response: WhatsAppResponse,
) -> WhatsAppResponseDB:
    """
    Saves WhatsApp responses to the database.
    """
    wa_response = WhatsAppResponseDB(
        incoming_id=response.incoming_id,
        response=response.response_text,
        response_datetime_utc=datetime.utcnow(),
        response_status=response.response_status,
    )
    asession.add(wa_response)
    await asession.commit()
    await asession.refresh(wa_response)
    return wa_response
