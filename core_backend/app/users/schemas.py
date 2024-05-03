from pydantic import BaseModel, ConfigDict


# not yet used.
class UserCreate(BaseModel):
    """
    Pydantic model for user creation
    """

    username: str
    password: str
    user_id: str
    retrieval_key: str

    model_config = ConfigDict(from_attributes=True)