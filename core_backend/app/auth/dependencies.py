from datetime import datetime, timedelta
from typing import Annotated, Dict, Optional, Union, cast

from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
    OAuth2PasswordBearer,
)
from jose import JWTError, jwt

from .config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_ALGORITHM,
    JWT_SECRET,
    USER1_PASSWORD,
    USER1_RETRIEVAL_SECRET,
    USER1_USERNAME,
    USER2_PASSWORD,
    USER2_RETRIEVAL_SECRET,
    USER2_USERNAME,
)
from .schemas import AccessLevel, AuthenticatedUser

bearer = HTTPBearer()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


USERS = {
    USER1_USERNAME: {
        "password": USER1_PASSWORD,
        "access_level": "fullaccess",
    },
    USER2_USERNAME: {
        "password": USER2_PASSWORD,
        "access_level": "fullaccess",
    },
}


def auth_bearer_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
) -> str:
    """
    Authenticate using basic bearer token. Used for calling
    the question-answering endpoints
    """
    token = credentials.credentials
    # change to "hash check against db" logic later
    if token not in [USER1_RETRIEVAL_SECRET, USER2_RETRIEVAL_SECRET]:
        raise HTTPException(status_code=401, detail="Invalid bearer token")
    else:
        return token  # NOT SURE ABOUT THIS - IS THIS REASONABLE?


def authenticate_user(*, username: str, password: str) -> Optional[AuthenticatedUser]:
    """
    Authenticate user using username and password.
    """
    if username not in USERS:
        return None

    if password == USERS[username]["password"]:
        access_level = cast(AccessLevel, USERS[username]["access_level"])
        return AuthenticatedUser(username=username, access_level=access_level)

    return None


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


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)]
) -> AuthenticatedUser:
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

        user = AuthenticatedUser(
            username=username,
            access_level=cast(AccessLevel, USERS[username]["access_level"]),
        )

    except JWTError as err:
        raise credentials_exception from err

    return user


def get_current_fullaccess_user(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> AuthenticatedUser:
    """
    Get the current active user if they have full access
    """
    if current_user.access_level != "fullaccess":
        raise HTTPException(status_code=400, detail="User does not have full access")
    return current_user


def get_current_readonly_user(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> AuthenticatedUser:
    """
    Get the current active user if they have readonly access
    """
    if current_user.access_level not in ["readonly", "fullaccess"]:
        raise HTTPException(
            status_code=400, detail="User does not have readonly or full access"
        )
    return current_user
