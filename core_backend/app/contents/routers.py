"""This module contains the FastAPI router for the content management endpoints."""

from typing import Annotated, List, Optional

import pandas as pd
from fastapi import APIRouter, Depends, UploadFile, status
from fastapi.exceptions import HTTPException
from pandas.errors import EmptyDataError, ParserError
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import get_current_user
from ..config import CHECK_CONTENT_LIMIT
from ..database import get_async_session
from ..tags.models import TagDB, get_list_of_tag_from_db, save_tag_to_db, validate_tags
from ..tags.schemas import TagCreate, TagRetrieve
from ..users.models import UserDB, get_content_quota_by_userid
from ..utils import setup_logger
from .models import (
    ContentDB,
    delete_content_from_db,
    get_content_from_db,
    get_list_of_content_from_db,
    save_content_to_db,
    update_content_in_db,
)
from .schemas import (
    ContentCreate,
    ContentRetrieve,
    CustomError,
    CustomErrorList,
)

router = APIRouter(prefix="/content", tags=["Content Management"])
logger = setup_logger()


class BulkUploadResponse(BaseModel):
    """
    Pydantic model for the csv-upload response
    """

    tags: List[TagRetrieve]
    contents: List[ContentRetrieve]


class ExceedsContentQuotaError(Exception):
    """
    Exception raised when a user is attempting to add
    more content that their quota allows.
    """


@router.post("/", response_model=ContentRetrieve)
async def create_content(
    content: ContentCreate,
    user_db: Annotated[UserDB, Depends(get_current_user)],
    asession: AsyncSession = Depends(get_async_session),
) -> Optional[ContentRetrieve]:
    """Create content endpoint. Calls embedding model to get content embedding and
    inserts it to PG database.

    :param content: `ContentCreate` object containing content details.
    :param user_db: `UserDB` object of the user making the request.
    :param asession: AsyncSession object for database transactions.

    :returns:
        `ContentRetrieve` object of the created content.

    :raises HTTPException: If the content tags are invalid or if the user would exceed
        their content quota.
    """

    is_tag_valid, content_tags = await validate_tags(
        user_db.user_id, content.content_tags, asession
    )
    if not is_tag_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid tag ids: {content_tags}",
        )
    content.content_tags = content_tags

    # Check if the user would exceed their content quota
    if CHECK_CONTENT_LIMIT:
        try:
            await _check_content_quota_availability(
                user_id=user_db.user_id,
                n_contents_to_add=1,
                asession=asession,
            )
        except ExceedsContentQuotaError as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Exceeds content quota for user. {e}",
            ) from e

    content_db = await save_content_to_db(
        user_id=user_db.user_id,
        content=content,
        asession=asession,
    )
    return _convert_record_to_schema(content_db)


@router.put("/{content_id}", response_model=ContentRetrieve)
async def edit_content(
    content_id: int,
    content: ContentCreate,
    user_db: Annotated[UserDB, Depends(get_current_user)],
    asession: AsyncSession = Depends(get_async_session),
) -> ContentRetrieve:
    """Edit content by ID endpoint.

    NB: Currently, we retrieve the content to be updated from the database even if it
    is archived and then check if it is archived. This allows us to return a 400 error
    informing the user that the content is archived and cannot be updated.

    :param content_id: The ID of the content to edit.
    :param content: `ContentCreate` object containing content details.
    :param user_db: `UserDB` object of the user making the request.
    :param asession: AsyncSession object for database transactions.

    :returns:
        `ContentRetrieve` object of the edited content.

    :raises HTTPException: If the content ID is not found in the database, if the
        content tags are invalid, or if the content to be updated is archived.
    """

    old_content = await get_content_from_db(
        user_id=user_db.user_id,
        content_id=content_id,
        exclude_archived=False,
        asession=asession,
    )

    if not old_content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Content id `{content_id}` not found",
        )
    if old_content.is_archived:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Content id `{content_id}` is archived and cannot be updated",
        )

    is_tag_valid, content_tags = await validate_tags(
        user_db.user_id, content.content_tags, asession
    )
    if not is_tag_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid tag ids: {content_tags}",
        )
    content.content_tags = content_tags
    updated_content = await update_content_in_db(
        user_id=user_db.user_id,
        content_id=content_id,
        content=content,
        asession=asession,
    )

    return _convert_record_to_schema(updated_content)


@router.get("/", response_model=List[ContentRetrieve])
async def retrieve_content(
    user_db: Annotated[UserDB, Depends(get_current_user)],
    skip: int = 0,
    limit: int = 50,
    exclude_archived: bool = True,
    asession: AsyncSession = Depends(get_async_session),
) -> List[ContentRetrieve]:
    """Retrieve all content endpoint.

    :param user_db: `UserDB` object of the user making the request.
    :param skip: Number of records to skip.
    :param limit: Number of records to retrieve.
    :param exclude_archived: Specifies whether to exclude archived content.
    :param asession: AsyncSession object for database transactions.

    :returns:
        contents: List of `ContentRetrieve` objects.
    """

    records = await get_list_of_content_from_db(
        user_id=user_db.user_id,
        offset=skip,
        limit=limit,
        exclude_archived=exclude_archived,
        asession=asession,
    )
    contents = [_convert_record_to_schema(c) for c in records]
    return contents


@router.delete("/{content_id}")
async def delete_content(
    content_id: int,
    user_db: Annotated[UserDB, Depends(get_current_user)],
    asession: AsyncSession = Depends(get_async_session),
) -> None:
    """Delete content by ID endpoint.

    :param content_id: The ID of the content to delete.
    :param user_db: `UserDB` object of the user making the request.
    :param asession: AsyncSession object for database transactions.

    :raises HTTPException: If the content ID is not found in the database.
    """

    record = await get_content_from_db(
        user_id=user_db.user_id,
        content_id=content_id,
        asession=asession,
    )

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Content id `{content_id}` not found",
        )
    await delete_content_from_db(
        user_id=user_db.user_id,
        content_id=content_id,
        asession=asession,
    )


@router.get("/{content_id}", response_model=ContentRetrieve)
async def retrieve_content_by_id(
    content_id: int,
    user_db: Annotated[UserDB, Depends(get_current_user)],
    asession: AsyncSession = Depends(get_async_session),
) -> ContentRetrieve:
    """Retrieve content by ID endpoint.

    :param content_id: The ID of the content to retrieve.
    :param user_db: `UserDB` object of the user making the request.
    :param asession: AsyncSession object for database transactions.

    :returns:
        `ContentRetrieve` object of the retrieved content.

    :raises HTTPException: If the content ID is not found in the database.
    """

    record = await get_content_from_db(
        user_id=user_db.user_id,
        content_id=content_id,
        asession=asession,
    )

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Content id `{content_id}` not found",
        )

    return _convert_record_to_schema(record)


@router.post("/csv-upload", response_model=BulkUploadResponse)
async def bulk_upload_contents(
    file: UploadFile,
    user_db: Annotated[UserDB, Depends(get_current_user)],
    asession: AsyncSession = Depends(get_async_session),
) -> Optional[BulkUploadResponse]:
    """Upload, check, and ingest contents in bulk from a CSV file.

    Note: If there are any issues with the CSV, the endpoint will return a 400 error
    with the list of issues under detail in the response body.

    :param file: The CSV file to upload.
    :param user_db: `UserDB` object of the user making the request.
    :param asession: AsyncSession object for database transactions.

    :returns:
        `BulkUploadResponse` object containing the tags and contents created.

    :raises HTTPException: If `file` is not a valid CSV file.
    """

    # Ensure the file is a CSV
    if file.filename is None or not file.filename.endswith(".csv"):
        error_list_model = CustomErrorList(
            errors=[
                CustomError(
                    type="invalid_format",
                    description="Please upload a CSV file.",
                )
            ]
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_list_model.model_dump(),
        )

    df = _load_csv(file)
    await _csv_checks(df=df, user_id=user_db.user_id, asession=asession)

    # Create each new tag in the database
    tags_col = "tags"
    created_tags: List[TagRetrieve] = []
    tag_name_to_id_map: dict[str, int] = {}
    skip_tags = tags_col not in df.columns or df[tags_col].isnull().all()
    if not skip_tags:
        incoming_tags = _extract_unique_tags(tags_col=df[tags_col])
        tags_in_db = await get_list_of_tag_from_db(
            user_id=user_db.user_id, asession=asession
        )
        tags_to_create = _get_tags_not_in_db(
            tags_in_db=tags_in_db, incoming_tags=incoming_tags
        )
        for tag in tags_to_create:
            tag_create = TagCreate(tag_name=tag)
            tag_db = await save_tag_to_db(
                user_id=user_db.user_id,
                tag=tag_create,
                asession=asession,
            )
            tags_in_db.append(tag_db)

            # Convert the tag record to a schema (for response)
            tag_retrieve = _convert_tag_record_to_schema(tag_db)
            created_tags.append(tag_retrieve)

        # tag name to tag id mapping
        tag_name_to_id_map = {tag.tag_name: tag.tag_id for tag in tags_in_db}

    # Add each row to the content database
    created_contents = []
    for _, row in df.iterrows():
        content_tags: List = []  # should be List[TagDB] but clashes with validate_tags
        if tag_name_to_id_map and not pd.isna(row[tags_col]):
            tag_names = [
                tag_name.strip().upper() for tag_name in row[tags_col].split(",")
            ]
            tag_ids = [tag_name_to_id_map[tag_name] for tag_name in tag_names]
            is_tag_valid, content_tags = await validate_tags(
                user_db.user_id, tag_ids, asession
            )

        content = ContentCreate(
            content_title=row["title"],
            content_text=row["text"],
            content_tags=content_tags,
            content_metadata={},
        )
        content_db = await save_content_to_db(
            user_id=user_db.user_id, content=content, asession=asession
        )
        content_retrieve = _convert_record_to_schema(content_db)
        created_contents.append(content_retrieve)

    return BulkUploadResponse(tags=created_tags, contents=created_contents)


def _load_csv(file: UploadFile) -> pd.DataFrame:
    """Load the CSV file into a pandas DataFrame.

    :param file: The CSV file to load.

    :returns:
        df: The loaded DataFrame.

    :raises HTTPException: If the CSV file is empty or unreadable.
    """

    try:
        df = pd.read_csv(file.file, dtype=str)
    except (EmptyDataError, ParserError, UnicodeDecodeError) as e:
        error_type = {
            EmptyDataError: "empty_data",
            ParserError: "parse_error",
            UnicodeDecodeError: "encoding_error",
        }.get(type(e), "unknown_error")
        error_description = {
            "empty_data": "The CSV file is empty",
            "parse_error": "CSV is unreadable (parsing error)",
            "encoding_error": "CSV is unreadable (encoding error)",
        }.get(error_type, "An unknown error occurred")
        error_list_model = CustomErrorList(
            errors=[CustomError(type=error_type, description=error_description)]
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_list_model.model_dump(),
        ) from e
    if df.empty:
        error_list_model = CustomErrorList(
            errors=[
                CustomError(type="no_rows_csv", description="The CSV file is empty")
            ]
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_list_model.model_dump(),
        )

    return df


async def _csv_checks(df: pd.DataFrame, user_id: int, asession: AsyncSession) -> None:
    """Perform checks on the CSV file to ensure it meets the requirements.

    :param df: The DataFrame to check.
    :param user_id: The user ID to check the content quota for.
    :param asession: The AsyncSession object for database transactions.

    :raises HTTPException: If the CSV file does not meet the requirements.
    """

    # check if title and text columns are present
    cols = df.columns
    error_list = []
    if not {"title", "text"}.issubset(cols):
        error_list.append(
            CustomError(
                type="missing_columns",
                description="File must have 'title' and 'text' columns.",
            )
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=CustomErrorList(errors=error_list).model_dump(),
        )

    # Check content quota availability
    try:
        await _check_content_quota_availability(
            user_id=user_id, n_contents_to_add=len(df), asession=asession
        )
    except ExceedsContentQuotaError as e:
        error_list.append(CustomError(type="exceeds_quota", description=str(e)))

    # strip columns to catch duplicates better and empty cells
    df["title"] = df["title"].str.strip()
    df["text"] = df["text"].str.strip()

    # set any empty strings to None
    df = df.replace("", None)

    # check if there are any empty values in either column
    if df["title"].isnull().any():
        error_list.append(
            CustomError(
                type="empty_title",
                description=("One or more empty content titles found in the CSV file."),
            )
        )
    if df["text"].isnull().any():
        error_list.append(
            CustomError(
                type="empty_text",
                description=("One or more empty content texts found in the CSV file."),
            )
        )

    # check if any title exceeds 150 characters
    if df["title"].str.len().max() > 150:
        error_list.append(
            CustomError(
                type="title_too_long",
                description="One or more content titles exceed 150 characters.",
            )
        )
    # check if any text exceeds 2000 characters
    if df["text"].str.len().max() > 2000:
        error_list.append(
            CustomError(
                type="texts_too_long",
                description="One or more content texts exceed 2000 characters.",
            )
        )

    # check if there are duplicates in either column
    if df.duplicated(subset=["title"]).any():
        error_list.append(
            CustomError(
                type="duplicate_titles",
                description="Duplicate content titles found in the CSV file.",
            )
        )
    if df.duplicated(subset=["text"]).any():
        error_list.append(
            CustomError(
                type="duplicate_texts",
                description="Duplicate content texts found in the CSV file.",
            )
        )

    # check for duplicate titles and texts between the CSV and the database
    contents_in_db = await get_list_of_content_from_db(
        user_id=user_id,
        offset=0,
        limit=None,
        exclude_archived=True,
        asession=asession,
    )

    content_titles_in_db = [c.content_title.strip() for c in contents_in_db]
    content_texts_in_db = [c.content_text.strip() for c in contents_in_db]
    if df["title"].isin(content_titles_in_db).any():
        error_list.append(
            CustomError(
                type="title_in_db",
                description=(
                    "One or more content titles already exist in the database."
                ),
            )
        )
    if df["text"].isin(content_texts_in_db).any():
        error_list.append(
            CustomError(
                type="text_in_db",
                description=(
                    "One or more content texts already exist in the database."
                ),
            )
        )

    if error_list:
        error_list_model = CustomErrorList(errors=error_list)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_list_model.model_dump(),
        )


async def _check_content_quota_availability(
    user_id: int,
    n_contents_to_add: int,
    asession: AsyncSession,
) -> None:
    """Raise an error if user would reach their content quota given n new contents.

    :param user_id: The user ID to check the content quota for.
    :param n_contents_to_add: The number of new contents to add.
    :param asession: The AsyncSession object for database transactions.

    :raises ExceedsContentQuotaError: If the user would exceed their content quota.
    """

    # get content_quota value for this user from UserDB
    content_quota = await get_content_quota_by_userid(
        user_id=user_id, asession=asession
    )

    # if content_quota is None, then there is no limit
    if content_quota is not None:
        # get the number of contents this user has already added
        stmt = select(ContentDB).where(ContentDB.user_id == user_id)
        user_contents = (await asession.execute(stmt)).all()
        n_contents_in_db = len(user_contents)

        # error if total of existing and new contents exceeds the quota
        if (n_contents_in_db + n_contents_to_add) > content_quota:
            raise ExceedsContentQuotaError(
                f"Adding {n_contents_to_add} new contents to the already existing "
                f"{n_contents_in_db} in the database would exceed the allowed limit "
                f"of {content_quota} contents."
            )


def _extract_unique_tags(tags_col: pd.Series) -> List[str]:
    """Get unique UPPERCASE tags from a DataFrame column (comma-separated within
    column).

    :param tags_col: The column containing tags.

    :returns:
        tags_unique_list: A list of unique tags.
    """

    # prep col
    tags_col = tags_col.dropna().astype(str)
    # split and explode to have one tag per row
    tags_flat = tags_col.str.split(",").explode()
    # strip and uppercase
    tags_flat = tags_flat.str.strip().str.upper()
    # get unique tags as a list
    tags_unique_list = tags_flat.unique().tolist()
    return tags_unique_list


def _get_tags_not_in_db(
    tags_in_db: List[TagDB],
    incoming_tags: List[str],
) -> List[str]:
    """Compare tags fetched from the DB with incoming tags and return tags not in the
    DB.

    :param tags_in_db: List of `TagDB` objects fetched from the database.
    :param incoming_tags: List of incoming tags.

    :returns:
        tags_not_in_db_list: List of tags not in the database.
    """

    tags_in_db_list = [tag_json.tag_name for tag_json in tags_in_db]
    tags_not_in_db_list = list(set(incoming_tags) - set(tags_in_db_list))

    return tags_not_in_db_list


def _convert_record_to_schema(record: ContentDB) -> ContentRetrieve:
    """Convert `models.ContentDB` models to `ContentRetrieve` schema.

    :param record: `ContentDB` object to convert.

    :returns:
        `ContentRetrieve` object of the converted record.
    """

    content_retrieve = ContentRetrieve(
        content_id=record.content_id,
        user_id=record.user_id,
        content_title=record.content_title,
        content_text=record.content_text,
        content_tags=[tag.tag_id for tag in record.content_tags],
        positive_votes=record.positive_votes,
        negative_votes=record.negative_votes,
        content_metadata=record.content_metadata,
        created_datetime_utc=record.created_datetime_utc,
        updated_datetime_utc=record.updated_datetime_utc,
    )

    return content_retrieve


def _convert_tag_record_to_schema(record: TagDB) -> TagRetrieve:
    """Convert `models.TagDB` models to `TagRetrieve` schema.

    :param record: `TagDB` object to convert.

    :returns:
        tag_retrieve: `TagRetrieve` object of the converted record.
    """

    tag_retrieve = TagRetrieve(
        tag_id=record.tag_id,
        user_id=record.user_id,
        tag_name=record.tag_name,
        created_datetime_utc=record.created_datetime_utc,
        updated_datetime_utc=record.updated_datetime_utc,
    )

    return tag_retrieve
