from typing import Annotated, List

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import get_current_fullaccess_user, get_current_readonly_user
from ..auth.schemas import AuthenticatedUser
from ..database import get_async_session
from ..users.models import get_user_by_username
from ..utils import setup_logger
from .models import (
    ContentDB,
    delete_content_from_db,
    get_content_from_db,
    get_list_of_content_from_db,
    save_content_to_db,
    update_content_in_db,
)
from .schemas import ContentCreate, ContentRetrieve

router = APIRouter(prefix="/content")
logger = setup_logger()


@router.post("/", response_model=ContentRetrieve)
async def create_content(
    content: ContentCreate,
    full_access_user: Annotated[
        AuthenticatedUser, Depends(get_current_fullaccess_user)
    ],
    asession: AsyncSession = Depends(get_async_session),
) -> ContentRetrieve | None:
    """
    Create content endpoint. Calls embedding model to get content embedding and
    upserts it to PG database
    """

    user = await get_user_by_username(full_access_user.username, asession)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    content_db = await save_content_to_db(
        user_id=user.user_id,
        content=content,
        asession=asession,
    )
    return _convert_record_to_schema(content_db)


@router.put("/{content_id}", response_model=ContentRetrieve)
async def edit_content(
    content_id: int,
    content: ContentCreate,
    full_access_user: Annotated[
        AuthenticatedUser, Depends(get_current_fullaccess_user)
    ],
    asession: AsyncSession = Depends(get_async_session),
) -> ContentRetrieve:
    """
    Edit content endpoint
    """

    user = await get_user_by_username(full_access_user.username, asession)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    old_content = await get_content_from_db(
        user_id=user.user_id,
        content_id=content_id,
        asession=asession,
    )

    if not old_content:
        raise HTTPException(
            status_code=404, detail=f"Content id `{content_id}` not found"
        )
    updated_content = await update_content_in_db(
        user_id=user.user_id,
        content_id=content_id,
        content=content,
        asession=asession,
    )

    return _convert_record_to_schema(updated_content)


@router.get("/", response_model=list[ContentRetrieve])
async def retrieve_content(
    readonly_access_user: Annotated[
        AuthenticatedUser, Depends(get_current_readonly_user)
    ],
    skip: int = 0,
    limit: int = 50,
    asession: AsyncSession = Depends(get_async_session),
) -> List[ContentRetrieve]:
    """
    Retrieve all content endpoint
    """

    user = await get_user_by_username(readonly_access_user.username, asession)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    records = await get_list_of_content_from_db(
        user_id=user.user_id,
        offset=skip,
        limit=limit,
        asession=asession,
    )
    contents = [_convert_record_to_schema(c) for c in records]
    return contents


@router.delete("/{content_id}")
async def delete_content(
    content_id: int,
    full_access_user: Annotated[
        AuthenticatedUser, Depends(get_current_fullaccess_user)
    ],
    asession: AsyncSession = Depends(get_async_session),
) -> None:
    """
    Delete content endpoint
    """

    user = await get_user_by_username(full_access_user.username, asession)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    record = await get_content_from_db(
        user_id=user.user_id,
        content_id=content_id,
        asession=asession,
    )

    if not record:
        raise HTTPException(
            status_code=404, detail=f"Content id `{content_id}` not found"
        )
    await delete_content_from_db(
        user_id=user.user_id,
        content_id=content_id,
        asession=asession,
    )


@router.get("/{content_id}", response_model=ContentRetrieve)
async def retrieve_content_by_id(
    content_id: int,
    readonly_access_user: Annotated[
        AuthenticatedUser, Depends(get_current_readonly_user)
    ],
    asession: AsyncSession = Depends(get_async_session),
) -> ContentRetrieve:
    """
    Retrieve content by id endpoint
    """

    user = await get_user_by_username(readonly_access_user.username, asession)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    record = await get_content_from_db(
        user_id=user.user_id,
        content_id=content_id,
        asession=asession,
    )

    if not record:
        raise HTTPException(
            status_code=404, detail=f"Content id `{content_id}` not found"
        )

    return _convert_record_to_schema(record)


def _convert_record_to_schema(record: ContentDB) -> ContentRetrieve:
    """
    Convert db_models.ContentDB models to ContentRetrieve schema
    """
    content_retrieve = ContentRetrieve(
        content_id=record.content_id,
        user_id=record.user_id,
        content_title=record.content_title,
        content_text=record.content_text,
        content_language=record.content_language,
        positive_votes=record.positive_votes,
        negative_votes=record.negative_votes,
        content_metadata=record.content_metadata,
        created_datetime_utc=record.created_datetime_utc,
        updated_datetime_utc=record.updated_datetime_utc,
    )

    return content_retrieve
