import hashlib
import logging
import os
import secrets
from logging import Logger
from typing import List, Optional
from uuid import uuid4

import aiohttp
import litellm
from litellm import aembedding

from .config import (
    LANGFUSE,
    LITELLM_API_KEY,
    LITELLM_ENDPOINT,
    LITELLM_MODEL_EMBEDDING,
    LOG_LEVEL,
)

# To make 32-byte API keys (results in 43 characters)
SECRET_KEY_N_BYTES = 32


# To prefix trace_id with project name
LANGFUSE_PROJECT_NAME = None

if LANGFUSE == "True":
    langFuseLogger = litellm.utils.langFuseLogger
    if langFuseLogger is None:
        langFuseLogger = litellm.integrations.langfuse.LangFuseLogger()
        LANGFUSE_PROJECT_NAME = (
            langFuseLogger.Langfuse.client.projects.get().data[0].name
        )
    elif isinstance(langFuseLogger, litellm.integrations.langfuse.LangFuseLogger):
        LANGFUSE_PROJECT_NAME = (
            langFuseLogger.Langfuse.client.projects.get().data[0].name
        )


def generate_key() -> str:
    """
    Generate API key (default 32 byte = 43 characters)
    """

    return secrets.token_urlsafe(SECRET_KEY_N_BYTES)


def get_key_hash(key: str) -> str:
    """Hashes the api key using SHA256."""
    return hashlib.sha256(key.encode()).hexdigest()


def get_password_salted_hash(key: str) -> str:
    """Hashes the password using SHA256 with a salt."""
    salt = os.urandom(16)
    key_salt_combo = salt + key.encode()
    hash_obj = hashlib.sha256(key_salt_combo)
    return salt.hex() + hash_obj.hexdigest()


def verify_password_salted_hash(key: str, stored_hash: str) -> bool:
    """Verifies if the api key matches the hash."""
    salt = bytes.fromhex(stored_hash[:32])
    original_hash = stored_hash[32:]
    key_salt_combo = salt + key.encode()
    hash_obj = hashlib.sha256(key_salt_combo)

    return hash_obj.hexdigest() == original_hash


def get_random_string(size: int) -> str:
    """Generate a random string of fixed length."""
    import random
    import string

    return "".join(random.choices(string.ascii_letters + string.digits, k=size))


def create_langfuse_metadata(query_id: int, user_id: int | None = None) -> dict:
    """Create metadata for langfuse logging."""
    trace_id_elements = ["query_id", str(query_id)]

    if LANGFUSE_PROJECT_NAME is not None:
        trace_id_elements.insert(0, LANGFUSE_PROJECT_NAME)

    metadata = {
        "trace_id": "-".join(trace_id_elements),
    }
    if user_id is not None:
        metadata["trace_user_id"] = "user_id-" + str(user_id)

    return metadata


def get_log_level_from_str(log_level_str: str = LOG_LEVEL) -> int:
    """
    Get log level from string
    """
    log_level_dict = {
        "CRITICAL": logging.CRITICAL,
        "ERROR": logging.ERROR,
        "WARNING": logging.WARNING,
        "INFO": logging.INFO,
        "DEBUG": logging.DEBUG,
        "NOTSET": logging.NOTSET,
    }

    return log_level_dict.get(log_level_str.upper(), logging.INFO)


def generate_secret_key() -> str:
    """
    Generate a secret key for the user query
    """
    return uuid4().hex


async def embedding(text_to_embed: str, metadata: Optional[dict] = None) -> List[float]:
    """
    Get embedding for the given text
    """
    if metadata is None:
        metadata = {}
    content_embedding = await aembedding(
        model=LITELLM_MODEL_EMBEDDING,
        input=text_to_embed,
        api_base=LITELLM_ENDPOINT,
        api_key=LITELLM_API_KEY,
        metadata=metadata,
    )

    return content_embedding.data[0]["embedding"]


def setup_logger(
    name: str = __name__, log_level: int = get_log_level_from_str()
) -> Logger:
    """
    Setup logger for the application
    """
    logger = logging.getLogger(name)

    # If the logger already has handlers,
    # assume it was already configured and return it.
    if logger.handlers:
        return logger

    logger.setLevel(log_level)

    formatter = logging.Formatter(
        "%(asctime)s %(filename)20s%(lineno)4s : %(message)s",
        datefmt="%m/%d/%Y %I:%M:%S %p",
    )

    handler = logging.StreamHandler()
    handler.setLevel(log_level)
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger


class HttpClient:
    """
    HTTP client for call other endpoints
    """

    session: aiohttp.ClientSession | None = None

    def start(self) -> None:
        """
        Create AIOHTTP session
        """
        self.session = aiohttp.ClientSession()

    async def stop(self) -> None:
        """
        Close AIOHTTP session
        """
        if self.session is not None:
            await self.session.close()
        self.session = None

    def __call__(self) -> aiohttp.ClientSession:
        """
        Get AIOHTTP session
        """
        assert self.session is not None
        return self.session


_HTTP_CLIENT: aiohttp.ClientSession | None = None


def get_http_client() -> aiohttp.ClientSession:
    """
    Get HTTP client
    """
    global _HTTP_CLIENT
    if _HTTP_CLIENT is None or _HTTP_CLIENT.closed:
        http_client = HttpClient()
        http_client.start()
        _HTTP_CLIENT = http_client()
    return _HTTP_CLIENT
