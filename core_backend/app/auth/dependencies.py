from datetime import datetime, timedelta
from typing import Annotated, Dict, Optional, Union

from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
    OAuth2PasswordBearer,
)
from jose import JWTError, jwt

from ..database import get_async_session_direct
from ..users.models import (
    UserDB,
    UserNotFoundError,
    get_user_by_token,
    get_user_by_username,
)
from ..utils import get_key_hash, setup_logger
from .config import ACCESS_TOKEN_EXPIRE_MINUTES, JWT_ALGORITHM, JWT_SECRET
from .schemas import AuthenticatedUser

logger = setup_logger()

bearer = HTTPBearer()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


async def auth_bearer_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
) -> UserDB:
    """
    Authenticate using basic bearer token. Used for calling
    the question-answering endpoints
    """
    token = credentials.credentials

    asession = await get_async_session_direct()
    try:
        user_db = await get_user_by_token(token, asession)
        return user_db
    except UserNotFoundError as err:
        raise HTTPException(status_code=401, detail="Invalid retrieval key") from err
    finally:
        await asession.aclose()


async def authenticate_user(
    *, username: str, password: str
) -> Optional[AuthenticatedUser]:
    """
    Authenticate user using username and password.
    """
    asession = await get_async_session_direct()
    try:
        user_db = await get_user_by_username(username, asession)
        await asession.aclose()
        if user_db.hashed_password == get_key_hash(password):
            # hardcode "fullaccess" now, but may use it in the future
            return AuthenticatedUser(username=username, access_level="fullaccess")
        else:
            return None
    except UserNotFoundError:
        return None
    finally:
        await asession.aclose()


def create_access_token(username: str) -> str:
    """
    Create an access token for the user
    """
    payload: Dict[str, Union[str, datetime]] = {}
    expire = datetime.utcnow() + timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))

    payload["exp"] = expire
    payload["iat"] = datetime.utcnow()
    payload["sub"] = username
    payload["type"] = "access_token"

    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> UserDB:
    """
    Get the current user from the access token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception

        # fetch user from database
        asession = await get_async_session_direct()
        try:
            user_db = await get_user_by_username(username, asession)
            await asession.aclose()
            return user_db
        except UserNotFoundError as err:
            await asession.aclose()
            raise credentials_exception from err
        finally:
            await asession.aclose()

    except JWTError as err:
        raise credentials_exception from err
