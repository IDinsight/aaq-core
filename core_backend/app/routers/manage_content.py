from typing import Annotated, List

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import get_current_fullaccess_user, get_current_readonly_user
from ..db.db_models import (
    ContentDB,
    delete_content_from_db,
    get_content_from_db,
    get_list_of_content_from_db,
    is_content_language_combination_unique,
    save_content_to_db,
    update_content_in_db,
)
from ..db.engine import get_async_session
from ..schemas import (
    AuthenticatedUser,
    ContentRetrieve,
    ContentTextCreate,
)
from ..utils import setup_logger

router = APIRouter(prefix="/content")
logger = setup_logger()


@router.post("/create", response_model=ContentRetrieve)
async def create_content(
    content: ContentTextCreate,
    full_access_user: Annotated[
        AuthenticatedUser, Depends(get_current_fullaccess_user)
    ],
    asession: AsyncSession = Depends(get_async_session),
) -> ContentRetrieve | None:
    """
    Create content endpoint. Calls embedding model to get content embedding and
    upserts it to PG database
    """
    if not (
        await is_content_language_combination_unique(
            content.content_id, content.language_id, asession
        )
    ):
        raise HTTPException(
            status_code=400,
            detail="Content and language combination already exists",
        )
    content_db = await save_content_to_db(content, asession)
    return _convert_record_to_schema(content_db)


@router.put("/{content_text_id}/edit", response_model=ContentRetrieve)
async def edit_content(
    content_text_id: int,
    content: ContentTextCreate,
    full_access_user: Annotated[
        AuthenticatedUser, Depends(get_current_fullaccess_user)
    ],
    asession: AsyncSession = Depends(get_async_session),
) -> ContentRetrieve:
    """
    Edit content endpoint
    """
    old_content = await get_content_from_db(
        content_text_id,
        asession,
    )

    if not old_content:
        raise HTTPException(
            status_code=404, detail=f"Content id `{content_text_id}` not found"
        )
    if old_content.language_id != content.language_id and not (
        await is_content_language_combination_unique(
            content.content_id, content.language_id, asession
        )
    ):
        raise HTTPException(
            status_code=400,
            detail="Content and language combination already exists",
        )

    updated_content = await update_content_in_db(
        content_text_id,
        content,
        asession,
    )

    return _convert_record_to_schema(updated_content)


@router.get("/list", response_model=list[ContentRetrieve])
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
    records = await get_list_of_content_from_db(
        offset=skip, limit=limit, asession=asession
    )
    contents = [_convert_record_to_schema(c) for c in records]
    return contents


@router.delete("/{content_text_id}/delete")
async def delete_content(
    content_text_id: int,
    full_access_user: Annotated[
        AuthenticatedUser, Depends(get_current_fullaccess_user)
    ],
    asession: AsyncSession = Depends(get_async_session),
) -> None:
    """
    Delete content endpoint
    """
    record = await get_content_from_db(
        content_text_id,
        asession,
    )

    if not record:
        raise HTTPException(
            status_code=404, detail=f"Content id `{content_text_id}` not found"
        )
    await delete_content_from_db(content_text_id, record.content_id, asession)


@router.get("/{content_text_id}", response_model=ContentRetrieve)
async def retrieve_content_by_id(
    content_text_id: int,
    readonly_access_user: Annotated[
        AuthenticatedUser, Depends(get_current_readonly_user)
    ],
    asession: AsyncSession = Depends(get_async_session),
) -> ContentRetrieve:
    """
    Retrieve content by id endpoint
    """

    record = await get_content_from_db(content_text_id, asession)

    if not record:
        raise HTTPException(
            status_code=404, detail=f"Content id `{content_text_id}` not found"
        )

    return _convert_record_to_schema(record)


def _convert_record_to_schema(record: ContentDB) -> ContentRetrieve:
    """
    Convert db_models.ContentDB models to ContentRetrieve schema
    """
    content_retrieve = ContentRetrieve(
        content_text_id=record.content_text_id,
        content_title=record.content_title,
        content_text=record.content_text,
        content_id=record.content_id,
        language_id=record.language_id,
        content_metadata=record.content_metadata,
        created_datetime_utc=record.created_datetime_utc,
        updated_datetime_utc=record.updated_datetime_utc,
    )

    return content_retrieve
