from pydantic import BaseModel, ConfigDict


class KeyResponse(BaseModel):
    """
    Pydantic model for key response
    """

    username: str
    retrieval_key: str
    model_config = ConfigDict(from_attributes=True)
